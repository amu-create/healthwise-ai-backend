"""
벡터스토어 성능 벤치마크 스크립트
"""
import os
import time
import sys
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import torch

# Django 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthwise.settings')

import django
django.setup()

def benchmark_vectorstore():
    print("=== 벡터스토어 성능 벤치마크 ===\n")
    
    # 임베딩 모델 로드
    print("임베딩 모델 로드 중...")
    start = time.time()
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"},
        encode_kwargs={'normalize_embeddings': True}
    )
    print(f"임베딩 모델 로드 시간: {time.time() - start:.2f}초\n")
    
    # 벡터스토어 로드
    vectorstore_path = os.path.join(os.path.dirname(__file__), "vectorstore")
    print(f"벡터스토어 로드 중: {vectorstore_path}")
    start = time.time()
    vectorstore = FAISS.load_local(
        vectorstore_path, 
        embeddings, 
        allow_dangerous_deserialization=True
    )
    print(f"벡터스토어 로드 시간: {time.time() - start:.2f}초")
    print(f"총 벡터 수: {vectorstore.index.ntotal}")
    print(f"벡터 차원: {vectorstore.index.d}")
    print(f"인덱스 타입: {type(vectorstore.index)}\n")
    
    # 테스트 쿼리
    test_queries = [
        "단백질이 많은 음식은 무엇인가요?",
        "스쿼트 운동 방법을 알려주세요",
        "스트레스 해소하는 방법은?",
        "다이어트에 좋은 식단 추천해주세요",
        "근육을 키우려면 어떻게 해야 하나요?",
        "유산소 운동의 효과는?",
        "비타민 D가 부족하면 어떻게 되나요?",
        "요가의 장점은 무엇인가요?",
        "하루에 물을 얼마나 마셔야 하나요?",
        "수면의 중요성에 대해 알려주세요"
    ]
    
    print("=== 검색 성능 테스트 ===\n")
    
    # 첫 번째 실행 (워밍업)
    print("워밍업 실행...")
    for query in test_queries[:3]:
        _ = vectorstore.similarity_search_with_score(query, k=3)
    
    # 실제 벤치마크
    print("\n실제 벤치마크:")
    total_time = 0
    results = []
    
    for query in test_queries:
        start = time.time()
        docs = vectorstore.similarity_search_with_score(query, k=3)
        elapsed = time.time() - start
        total_time += elapsed
        
        results.append({
            'query': query,
            'time': elapsed,
            'num_results': len(docs),
            'top_score': docs[0][1] if docs else None
        })
        
        print(f"쿼리: '{query}'")
        print(f"  소요시간: {elapsed:.3f}초")
        print(f"  결과 수: {len(docs)}")
        if docs:
            print(f"  최상위 점수: {docs[0][1]:.3f}")
            print(f"  최상위 내용: {docs[0][0].page_content[:100]}...")
        print()
    
    # 통계
    print("\n=== 통계 ===")
    print(f"총 쿼리 수: {len(test_queries)}")
    print(f"총 소요시간: {total_time:.3f}초")
    print(f"평균 쿼리 시간: {total_time/len(test_queries):.3f}초")
    
    # 시간별 정렬
    results.sort(key=lambda x: x['time'])
    print(f"가장 빠른 쿼리: '{results[0]['query']}' ({results[0]['time']:.3f}초)")
    print(f"가장 느린 쿼리: '{results[-1]['query']}' ({results[-1]['time']:.3f}초)")


if __name__ == "__main__":
    benchmark_vectorstore()
