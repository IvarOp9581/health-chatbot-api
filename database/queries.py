"""
Database Query Functions
Optimized queries for food search, FTS, and nutritional analysis
"""

import aiosqlite
from pathlib import Path
from typing import List, Dict, Optional

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "health_data.db"

async def search_foods_by_name(query: str, limit: int = 10) -> List[Dict]:
    """
    Search foods using Full-Text Search (FTS5)
    Returns matching foods with nutritional info
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Sanitize FTS query - escape special characters and wrap in quotes
        # FTS5 special chars: - (NOT), OR, AND, NEAR, etc.
        # Remove or escape them to avoid syntax errors
        sanitized_query = query.strip()
        
        # Remove FTS operators that might cause issues
        fts_operators = ['OR', 'AND', 'NOT', 'NEAR']
        for op in fts_operators:
            sanitized_query = sanitized_query.replace(f' {op} ', ' ')
        
        # Wrap in quotes to treat as phrase search (handles hyphens, etc.)
        sanitized_query = f'"{sanitized_query}"'
        
        try:
            cursor = await db.execute("""
                SELECT f.id, f.fdc_id, f.description, f.protein, f.calories, 
                       f.sugar, f.sodium, f.portion_description, f.gram_weight
                FROM foods_fts
                JOIN foods f ON foods_fts.rowid = f.id
                WHERE foods_fts.description MATCH ?
                LIMIT ?
            """, (sanitized_query, limit))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            # If FTS fails, fallback to LIKE search
            print(f"FTS search failed for '{query}': {e}, using LIKE fallback")
            cursor = await db.execute("""
                SELECT id, fdc_id, description, protein, calories, 
                       sugar, sodium, portion_description, gram_weight
                FROM foods
                WHERE LOWER(description) LIKE ?
                LIMIT ?
            """, (f'%{query.lower()}%', limit))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_food_by_id(fdc_id: int) -> List[Dict]:
    """Get all portions for a specific food by FDC ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        cursor = await db.execute("""
            SELECT id, fdc_id, description, protein, calories, sugar, sodium,
                   portion_description, gram_weight
            FROM foods
            WHERE fdc_id = ?
        """, (fdc_id,))
        
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def find_similar_foods(
    protein: float,
    calories: float,
    exclude_keywords: List[str] = None,
    limit: int = 10
) -> List[Dict]:
    """
    Find foods with similar nutritional profile
    Useful for allergy substitutions
    """
    exclude_keywords = exclude_keywords or []
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Build exclusion clause
        exclusion_clause = " AND ".join([
            f"LOWER(description) NOT LIKE '%{keyword.lower()}%'"
            for keyword in exclude_keywords
        ])
        
        where_clause = f"WHERE {exclusion_clause}" if exclusion_clause else ""
        
        query = f"""
            SELECT DISTINCT fdc_id, description, protein, calories, sugar, sodium,
                   portion_description, gram_weight,
                   ABS(protein - ?) + ABS(calories - ?) as similarity_score
            FROM foods
            {where_clause}
            ORDER BY similarity_score ASC
            LIMIT ?
        """
        
        cursor = await db.execute(query, (protein, calories, limit))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_foods_by_category(
    categories: List[str],
    exclude_keywords: List[str] = None,
    limit_per_category: int = 10
) -> List[Dict]:
    """
    Get diverse foods from different categories for meal planning
    Categories are matched using FTS
    """
    exclude_keywords = exclude_keywords or []
    results = []
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        for category in categories:
            # Build exclusion clause
            exclusion_parts = [
                f"LOWER(f.description) NOT LIKE '%{keyword.lower()}%'"
                for keyword in exclude_keywords
            ]
            exclusion_clause = " AND " + " AND ".join(exclusion_parts) if exclusion_parts else ""
            
            query = f"""
                SELECT DISTINCT f.fdc_id, f.description, f.protein, f.calories,
                       f.sugar, f.sodium, f.portion_description, f.gram_weight
                FROM foods_fts
                JOIN foods f ON foods_fts.rowid = f.id
                WHERE foods_fts.description MATCH ?{exclusion_clause}
                LIMIT ?
            """
            
            cursor = await db.execute(query, (category, limit_per_category))
            rows = await cursor.fetchall()
            results.extend([dict(row) for row in rows])
    
    return results

async def get_random_diverse_foods(
    count: int = 50,
    exclude_keywords: List[str] = None
) -> List[Dict]:
    """
    Get random diverse foods for meal plan generation
    Excludes foods matching allergen keywords
    """
    exclude_keywords = exclude_keywords or []
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Build exclusion clause
        exclusion_parts = [
            f"LOWER(description) NOT LIKE '%{keyword.lower()}%'"
            for keyword in exclude_keywords
        ]
        exclusion_clause = "WHERE " + " AND ".join(exclusion_parts) if exclusion_parts else ""
        
        query = f"""
            SELECT DISTINCT fdc_id, description, protein, calories, sugar, sodium,
                   portion_description, gram_weight
            FROM foods
            {exclusion_clause}
            ORDER BY RANDOM()
            LIMIT ?
        """
        
        cursor = await db.execute(query, (count,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def search_by_nutrient_range(
    nutrient: str,  # 'calories', 'protein', 'sugar', 'sodium'
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    limit: int = 20
) -> List[Dict]:
    """
    Search foods within a specific nutrient range
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        conditions = []
        params = []
        
        if min_value is not None:
            conditions.append(f"{nutrient} >= ?")
            params.append(min_value)
        
        if max_value is not None:
            conditions.append(f"{nutrient} <= ?")
            params.append(max_value)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        params.append(limit)
        
        query = f"""
            SELECT id, fdc_id, description, protein, calories, sugar, sodium,
                   portion_description, gram_weight
            FROM foods
            {where_clause}
            ORDER BY {nutrient} ASC
            LIMIT ?
        """
        
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_database_stats() -> Dict:
    """Get database statistics for health check"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM foods")
        total_foods = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(DISTINCT fdc_id) FROM foods")
        unique_foods = (await cursor.fetchone())[0]
        
        return {
            "total_rows": total_foods,
            "unique_foods": unique_foods,
            "database_path": str(DB_PATH),
            "status": "connected"
        }
