import sqlite3
import json
import hashlib
import os
from contextlib import contextmanager
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "veggie_recipes.db")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                cuisine TEXT,
                vegetables TEXT,
                servings TEXT,
                prep_time TEXT,
                cook_time TEXT,
                difficulty TEXT,
                calories TEXT,
                ingredients TEXT,
                instructions TEXT,
                nutrition TEXT,
                tips TEXT,
                substitutions TEXT,
                storage TEXT,
                image_data TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                recipe_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(user_id, recipe_id),
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS nutrition_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                age TEXT,
                gender TEXT,
                height TEXT,
                weight TEXT,
                activity_level TEXT,
                dietary_preference TEXT,
                allergies TEXT,
                health_goal TEXT,
                calorie_target TEXT,
                macros TEXT,
                hydration_goal TEXT,
                meal_plan TEXT,
                recommended_vegetables TEXT,
                substitutions TEXT,
                weekly_tips TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS nutrition_favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(user_id, plan_id),
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (plan_id) REFERENCES nutrition_plans (id) ON DELETE CASCADE
            )
        """)
        _migrate_users_table()


# auth 

def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()


def create_user(username: str, email: str, password: str):
    salt = os.urandom(16).hex()
    pw_hash = _hash_password(password, salt)
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO users (username, email, password_hash, salt, created_at) VALUES (?, ?, ?, ?, ?)",
                (username, email, pw_hash, salt, datetime.utcnow().isoformat()),
            )
        return True, "Account created successfully."
    except sqlite3.IntegrityError:
        return False, "Username or email already exists."


def verify_user(username: str, password: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if row is None:
        return None
    if _hash_password(password, row["salt"]) == row["password_hash"]:
        return dict(row)
    return None


def get_user_by_id(user_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


# recipes

def save_recipe(user_id: int, recipe: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO recipes
               (user_id, title, cuisine, vegetables, servings, prep_time, cook_time,
                difficulty, calories, ingredients, instructions, nutrition, tips,
                substitutions, storage, image_data, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                user_id,
                recipe.get("title", "Untitled Recipe"),
                recipe.get("cuisine", ""),
                ", ".join(recipe.get("vegetables", [])) if isinstance(recipe.get("vegetables"), list) else recipe.get("vegetables", ""),
                recipe.get("servings", ""),
                recipe.get("prep_time", ""),
                recipe.get("cook_time", ""),
                recipe.get("difficulty", ""),
                recipe.get("calories", ""),
                json.dumps(recipe.get("ingredients", [])),
                json.dumps(recipe.get("instructions", [])),
                json.dumps(recipe.get("nutrition", {})),
                json.dumps(recipe.get("tips", [])),
                json.dumps(recipe.get("substitutions", [])),
                recipe.get("storage", ""),
                recipe.get("image_data", ""),
                datetime.utcnow().isoformat(),
            ),
        )
        return cur.lastrowid


def _row_to_recipe(row) -> dict:
    d = dict(row)
    for field in ("ingredients", "instructions", "nutrition", "tips", "substitutions"):
        try:
            d[field] = json.loads(d[field]) if d[field] else ([] if field != "nutrition" else {})
        except (json.JSONDecodeError, TypeError):
            d[field] = [] if field != "nutrition" else {}
    return d


def get_user_recipes(user_id: int, search: str = "", cuisine_filter: str = "All", difficulty_filter: str = "All"):
    query = "SELECT * FROM recipes WHERE user_id = ?"
    params = [user_id]
    if search:
        query += " AND (title LIKE ? OR vegetables LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    if cuisine_filter != "All":
        query += " AND cuisine = ?"
        params.append(cuisine_filter)
    if difficulty_filter != "All":
        query += " AND difficulty = ?"
        params.append(difficulty_filter)
    query += " ORDER BY created_at DESC"
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    return [_row_to_recipe(r) for r in rows]


def get_recipe(recipe_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
    return _row_to_recipe(row) if row else None


def delete_recipe(recipe_id: int, user_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM recipes WHERE id = ? AND user_id = ?", (recipe_id, user_id))


def get_distinct_cuisines(user_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT cuisine FROM recipes WHERE user_id = ? AND cuisine != ''", (user_id,)
        ).fetchall()
    return sorted({r["cuisine"] for r in rows})


#  favorites 

def toggle_favorite(user_id: int, recipe_id: int) -> bool:
    """Returns True if now favorited, False if removed."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM favorites WHERE user_id = ? AND recipe_id = ?", (user_id, recipe_id)
        ).fetchone()
        if row:
            conn.execute("DELETE FROM favorites WHERE id = ?", (row["id"],))
            return False
        conn.execute(
            "INSERT INTO favorites (user_id, recipe_id, created_at) VALUES (?, ?, ?)",
            (user_id, recipe_id, datetime.utcnow().isoformat()),
        )
        return True


def is_favorite(user_id: int, recipe_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM favorites WHERE user_id = ? AND recipe_id = ?", (user_id, recipe_id)
        ).fetchone()
    return row is not None


def get_favorite_recipes(user_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT r.* FROM recipes r
               JOIN favorites f ON r.id = f.recipe_id
               WHERE f.user_id = ?
               ORDER BY f.created_at DESC""",
            (user_id,),
        ).fetchall()
    return [_row_to_recipe(r) for r in rows]


def get_user_stats(user_id: int) -> dict:
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) c FROM recipes WHERE user_id = ?", (user_id,)).fetchone()["c"]
        favs = conn.execute("SELECT COUNT(*) c FROM favorites WHERE user_id = ?", (user_id,)).fetchone()["c"]
        cuisines = conn.execute(
            "SELECT COUNT(DISTINCT cuisine) c FROM recipes WHERE user_id = ? AND cuisine != ''", (user_id,)
        ).fetchone()["c"]
    return {"total_recipes": total, "total_favorites": favs, "unique_cuisines": cuisines}



# profile management

def _migrate_users_table():
    with get_conn() as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
        if "display_name" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN display_name TEXT DEFAULT ''")
        if "profile_picture" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN profile_picture TEXT DEFAULT ''")
        if "phone" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN phone TEXT DEFAULT ''")
        if "location" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN location TEXT DEFAULT ''")
        if "bio" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN bio TEXT DEFAULT ''")


def update_user_profile(
    user_id: int,
    username: str,
    display_name: str,
    email: str,
    phone: str = "",
    location: str = "",
    bio: str = "",
    profile_picture=None,
):
    try:
        with get_conn() as conn:
            if profile_picture is not None:
                conn.execute(
                    """UPDATE users SET username=?, display_name=?, email=?, phone=?,
                       location=?, bio=?, profile_picture=? WHERE id=?""",
                    (username, display_name, email, phone, location, bio, profile_picture, user_id),
                )
            else:
                conn.execute(
                    """UPDATE users SET username=?, display_name=?, email=?, phone=?,
                       location=?, bio=? WHERE id=?""",
                    (username, display_name, email, phone, location, bio, user_id),
                )
        return True, "Profile updated."
    except sqlite3.IntegrityError:
        return False, "Username or email already in use by another account."


def update_user_password(user_id: int, current_password: str, new_password: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if row is None:
        return False, "User not found."
    if _hash_password(current_password, row["salt"]) != row["password_hash"]:
        return False, "Current password is incorrect."
    new_salt = os.urandom(16).hex()
    new_hash = _hash_password(new_password, new_salt)
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET password_hash=?, salt=? WHERE id=?",
            (new_hash, new_salt, user_id),
        )
    return True, "Password changed successfully."


def delete_user(user_id: int):
    try:
        with get_conn() as conn:
            conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        return True
    except Exception:
        return False


# nutrition assistant

def save_nutrition_plan(user_id: int, profile: dict, plan: dict) -> int:
    """Persist a generated nutrition/meal plan. `profile` holds the raw
    inputs the user submitted; `plan` holds the AI-generated recommendation
    (already validated/parsed JSON from gemini_helper.generate_nutrition_plan).
    """
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO nutrition_plans
               (user_id, age, gender, height, weight, activity_level,
                dietary_preference, allergies, health_goal, calorie_target,
                macros, hydration_goal, meal_plan, recommended_vegetables,
                substitutions, weekly_tips, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                user_id,
                str(profile.get("age", "")),
                profile.get("gender", ""),
                str(profile.get("height", "")),
                str(profile.get("weight", "")),
                profile.get("activity_level", ""),
                profile.get("dietary_preference", ""),
                profile.get("allergies", ""),
                profile.get("health_goal", ""),
                plan.get("calorie_target", ""),
                json.dumps(plan.get("macros", {})),
                plan.get("hydration_goal", ""),
                json.dumps(plan.get("meal_plan", {})),
                json.dumps(plan.get("recommended_vegetables", [])),
                json.dumps(plan.get("substitutions", [])),
                json.dumps(plan.get("weekly_tips", [])),
                datetime.utcnow().isoformat(),
            ),
        )
        return cur.lastrowid


def _row_to_nutrition_plan(row) -> dict:
    d = dict(row)
    for field in ("macros", "meal_plan", "recommended_vegetables", "substitutions", "weekly_tips"):
        try:
            d[field] = json.loads(d[field]) if d[field] else ({} if field in ("macros", "meal_plan") else [])
        except (json.JSONDecodeError, TypeError):
            d[field] = {} if field in ("macros", "meal_plan") else []
    return d


def get_nutrition_plan(plan_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM nutrition_plans WHERE id = ?", (plan_id,)).fetchone()
    return _row_to_nutrition_plan(row) if row else None


def get_user_nutrition_plans(user_id: int, limit: int = 20):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM nutrition_plans WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [_row_to_nutrition_plan(r) for r in rows]


def delete_nutrition_plan(plan_id: int, user_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM nutrition_plans WHERE id = ? AND user_id = ?", (plan_id, user_id))


def toggle_nutrition_favorite(user_id: int, plan_id: int) -> bool:
    """Returns True if now favorited, False if removed."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM nutrition_favorites WHERE user_id = ? AND plan_id = ?", (user_id, plan_id)
        ).fetchone()
        if row:
            conn.execute("DELETE FROM nutrition_favorites WHERE id = ?", (row["id"],))
            return False
        conn.execute(
            "INSERT INTO nutrition_favorites (user_id, plan_id, created_at) VALUES (?, ?, ?)",
            (user_id, plan_id, datetime.utcnow().isoformat()),
        )
        return True


def is_nutrition_favorite(user_id: int, plan_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM nutrition_favorites WHERE user_id = ? AND plan_id = ?", (user_id, plan_id)
        ).fetchone()
    return row is not None


def get_favorite_nutrition_plans(user_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT p.* FROM nutrition_plans p
               JOIN nutrition_favorites f ON p.id = f.plan_id
               WHERE f.user_id = ?
               ORDER BY f.created_at DESC""",
            (user_id,),
        ).fetchall()
    return [_row_to_nutrition_plan(r) for r in rows]


def match_recipes_for_vegetables(user_id: int, vegetable_names: list, limit: int = 6):
    """Cross-reference the AI's recommended vegetables against this user's
    existing saved recipes (from the regular Generate Recipe feature), so
    the Nutrition Assistant can surface recipes that already exist instead
    of always generating new ones."""
    if not vegetable_names:
        return []
    with get_conn() as conn:
        clauses = " OR ".join(["vegetables LIKE ?"] * len(vegetable_names))
        params = [user_id] + [f"%{v}%" for v in vegetable_names]
        rows = conn.execute(
            f"SELECT * FROM recipes WHERE user_id = ? AND ({clauses}) ORDER BY created_at DESC LIMIT ?",
            params + [limit],
        ).fetchall()
    return [_row_to_recipe(r) for r in rows]