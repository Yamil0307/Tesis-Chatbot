import sqlite3
import json

def generate_evaluation_report():
    conn = sqlite3.connect("checkpoints.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            ROUND(AVG(faithfulness), 3) as avg_faith,
            ROUND(AVG(retrieval_relevance), 3) as avg_relev,
            ROUND(AVG(answer_quality), 3) as avg_qual,
            ROUND(MIN(faithfulness), 3) as min_faith,
            ROUND(MIN(retrieval_relevance), 3) as min_relev,
            ROUND(MIN(answer_quality), 3) as min_qual,
            ROUND(MAX(faithfulness), 3) as max_faith,
            ROUND(MAX(retrieval_relevance), 3) as max_relev,
            ROUND(MAX(answer_quality), 3) as max_qual
        FROM evaluations
    """)
    
    row = cursor.fetchone()
    print("\n" + "="*55)
    print("       REPORTE GLOBAL DEL SISTEMA RAG")
    print("="*55)
    print(f"  Total de consultas evaluadas: {row[0]}")
    print(f"\n  {'Métrica':<25} {'Mín':>6} {'Prom':>6} {'Máx':>6}")
    print(f"  {'-'*45}")
    print(f"  {'Faithfulness':<25} {row[4]:>6} {row[1]:>6} {row[7]:>6}")
    print(f"  {'Retrieval Relevance':<25} {row[5]:>6} {row[2]:>6} {row[8]:>6}")
    print(f"  {'Answer Quality':<25} {row[6]:>6} {row[3]:>6} {row[9]:>6}")
    
    # Por categoría (basado en los scores que asignamos)
    print("\n" + "="*55)
    print("       DISTRIBUCIÓN POR CATEGORÍA")
    print("="*55)
    
    # Correctas: quality >= 0.8
    cursor.execute("""
        SELECT COUNT(*), ROUND(AVG(faithfulness),3), 
               ROUND(AVG(retrieval_relevance),3), ROUND(AVG(answer_quality),3)
        FROM evaluations WHERE answer_quality >= 0.8
    """)
    r = cursor.fetchone()
    print(f"\n  ✅ Respuestas correctas (quality ≥ 0.8)")
    print(f"     N={r[0]} | faith={r[1]} | relev={r[2]} | qual={r[3]}")
    
    # Name mismatch: quality = 0.5
    cursor.execute("""
        SELECT COUNT(*), ROUND(AVG(faithfulness),3),
               ROUND(AVG(retrieval_relevance),3), ROUND(AVG(answer_quality),3)
        FROM evaluations WHERE answer_quality = 0.5
    """)
    r = cursor.fetchone()
    print(f"\n  ⚠️  Name mismatch (quality = 0.5)")
    print(f"     N={r[0]} | faith={r[1]} | relev={r[2]} | qual={r[3]}")
    
    # Retrieval fail: quality <= 0.1
    cursor.execute("""
        SELECT COUNT(*), ROUND(AVG(faithfulness),3),
               ROUND(AVG(retrieval_relevance),3), ROUND(AVG(answer_quality),3)
        FROM evaluations WHERE answer_quality <= 0.1
    """)
    r = cursor.fetchone()
    print(f"\n  ❌ Fallo de retrieval (quality ≤ 0.1)")
    print(f"     N={r[0]} | faith={r[1]} | relev={r[2]} | qual={r[3]}")
    
    conn.close()

if __name__ == "__main__":
    generate_evaluation_report()
