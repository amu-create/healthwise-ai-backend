"""
벡터스토어 최적화 스크립트
- IVF 인덱스 적용
- 메타데이터 추가
- 청크 크기 조정
"""
import os
import pickle
import numpy as np
import faiss
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import torch
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorstoreOptimizer:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.embedding_model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        self.vectorstore_path = os.path.join(os.path.dirname(__file__), "vectorstore")
        self.optimized_path = os.path.join(os.path.dirname(__file__), "vectorstore_optimized")
        
    def load_embeddings(self):
        """임베딩 모델 로드"""
        logger.info("임베딩 모델 로드 중...")
        return HuggingFaceEmbeddings(
            model_name=self.embedding_model_name,
            model_kwargs={"device": self.device},
            encode_kwargs={'normalize_embeddings': True, 'batch_size': 32}
        )
    
    def analyze_current_vectorstore(self):
        """현재 벡터스토어 분석"""
        logger.info("현재 벡터스토어 분석 중...")
        
        # 기존 벡터스토어 로드
        embeddings = self.load_embeddings()
        vectorstore = FAISS.load_local(
            self.vectorstore_path, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        
        # 통계 정보
        num_vectors = vectorstore.index.ntotal
        dimension = vectorstore.index.d
        
        logger.info(f"총 벡터 수: {num_vectors}")
        logger.info(f"벡터 차원: {dimension}")
        logger.info(f"현재 인덱스 타입: {type(vectorstore.index)}")
        
        # 문서 내용 분석
        if hasattr(vectorstore, 'docstore'):
            docs = []
            for i in range(min(10, num_vectors)):
                try:
                    doc_id = vectorstore.index_to_docstore_id.get(i)
                    if doc_id:
                        doc = vectorstore.docstore.search(doc_id)
                        if doc:
                            docs.append(doc)
                except:
                    pass
            
            if docs:
                avg_length = sum(len(doc.page_content) for doc in docs) / len(docs)
                logger.info(f"평균 문서 길이: {avg_length:.0f}자")
                
                # 카테고리 분석
                categories = set()
                for doc in docs:
                    if hasattr(doc, 'metadata') and 'source' in doc.metadata:
                        if 'exercise' in doc.metadata['source'].lower():
                            categories.add('exercise')
                        elif 'nutrition' in doc.metadata['source'].lower():
                            categories.add('nutrition')
                        elif 'health' in doc.metadata['source'].lower():
                            categories.add('health')
                
                logger.info(f"발견된 카테고리: {categories}")
        
        return vectorstore, num_vectors, dimension
    
    def create_ivf_index(self, vectorstore, num_vectors, dimension):
        """IVF 인덱스 생성"""
        logger.info("IVF 인덱스 생성 중...")
        
        # 최적 nlist 계산
        nlist = min(100, int(4 * np.sqrt(num_vectors)))
        logger.info(f"nlist 값: {nlist}")
        
        # 벡터 추출
        vectors = []
        for i in range(num_vectors):
            try:
                vec = vectorstore.index.reconstruct(i)
                vectors.append(vec)
            except:
                logger.warning(f"벡터 {i} 추출 실패")
        
        vectors = np.array(vectors).astype('float32')
        logger.info(f"추출된 벡터: {vectors.shape}")
        
        # IVF 인덱스 생성
        quantizer = faiss.IndexFlatL2(dimension)
        index_ivf = faiss.IndexIVFFlat(quantizer, dimension, nlist)
        
        # 학습
        logger.info("IVF 인덱스 학습 중...")
        index_ivf.train(vectors)
        
        # 벡터 추가
        logger.info("벡터 추가 중...")
        index_ivf.add(vectors)
        
        # nprobe 설정 (검색 시 탐색할 클러스터 수)
        index_ivf.nprobe = 10
        
        logger.info(f"IVF 인덱스 생성 완료: {index_ivf.ntotal} 벡터")
        
        return index_ivf
    
    def add_metadata_to_documents(self, vectorstore):
        """문서에 메타데이터 추가"""
        logger.info("메타데이터 추가 중...")
        
        # 카테고리 키워드 정의
        category_keywords = {
            'exercise': ['운동', '스쿼트', '푸시업', '플랭크', '런닝', '요가', '필라테스', '근육', '체력'],
            'nutrition': ['영양', '단백질', '탄수화물', '지방', '비타민', '칼로리', '식단', '음식', '다이어트'],
            'health': ['건강', '질병', '증상', '치료', '예방', '면역', '스트레스', '수면', '정신건강'],
            'general': []  # 기본 카테고리
        }
        
        updated_docs = []
        
        # 문서 처리
        for i in range(vectorstore.index.ntotal):
            try:
                doc_id = vectorstore.index_to_docstore_id.get(i)
                if doc_id:
                    doc = vectorstore.docstore.search(doc_id)
                    if doc and isinstance(doc, Document):
                        # 카테고리 결정
                        content_lower = doc.page_content.lower()
                        category = 'general'
                        max_count = 0
                        
                        for cat, keywords in category_keywords.items():
                            if cat == 'general':
                                continue
                            count = sum(1 for keyword in keywords if keyword in content_lower)
                            if count > max_count:
                                max_count = count
                                category = cat
                        
                        # 메타데이터 업데이트
                        if not hasattr(doc, 'metadata'):
                            doc.metadata = {}
                        
                        doc.metadata['category'] = category
                        doc.metadata['chunk_size'] = len(doc.page_content)
                        doc.metadata['indexed_at'] = time.time()
                        
                        updated_docs.append(doc)
                        
                        if i % 100 == 0:
                            logger.info(f"처리 중: {i}/{vectorstore.index.ntotal}")
            except Exception as e:
                logger.error(f"문서 {i} 처리 실패: {str(e)}")
        
        logger.info(f"메타데이터 추가 완료: {len(updated_docs)}개 문서")
        return updated_docs
    
    def create_optimized_vectorstore(self, documents, embeddings):
        """최적화된 벡터스토어 생성"""
        logger.info("최적화된 벡터스토어 생성 중...")
        
        # 청크 크기 500자로 재분할
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        # 문서 재분할
        split_docs = []
        for doc in documents:
            if len(doc.page_content) > 500:
                # 긴 문서는 분할
                chunks = text_splitter.split_text(doc.page_content)
                for i, chunk in enumerate(chunks):
                    new_doc = Document(
                        page_content=chunk,
                        metadata={
                            **doc.metadata,
                            'chunk_index': i,
                            'original_length': len(doc.page_content)
                        }
                    )
                    split_docs.append(new_doc)
            else:
                # 짧은 문서는 그대로
                split_docs.append(doc)
        
        logger.info(f"문서 분할 완료: {len(documents)}개 → {len(split_docs)}개")
        
        # 새 벡터스토어 생성
        vectorstore = FAISS.from_documents(split_docs, embeddings)
        
        return vectorstore
    
    def optimize_vectorstore(self):
        """전체 최적화 프로세스"""
        logger.info("=== 벡터스토어 최적화 시작 ===")
        
        try:
            # 1. 현재 벡터스토어 분석
            old_vectorstore, num_vectors, dimension = self.analyze_current_vectorstore()
            
            # 2. 벤치마크 - 기존 성능
            logger.info("\n--- 기존 벡터스토어 성능 테스트 ---")
            test_queries = [
                "단백질이 많은 음식은?",
                "스쿼트 운동 방법",
                "스트레스 해소법"
            ]
            
            for query in test_queries:
                start_time = time.time()
                results = old_vectorstore.similarity_search_with_score(query, k=3)
                elapsed = time.time() - start_time
                logger.info(f"쿼리: '{query}' - 소요시간: {elapsed:.3f}초")
            
            # 3. 문서에 메타데이터 추가
            documents = self.add_metadata_to_documents(old_vectorstore)
            
            # 4. 임베딩 모델 로드
            embeddings = self.load_embeddings()
            
            # 5. 최적화된 벡터스토어 생성 (청크 500자)
            optimized_vectorstore = self.create_optimized_vectorstore(documents, embeddings)
            
            # 6. IVF 인덱스 적용
            ivf_index = self.create_ivf_index(
                optimized_vectorstore, 
                optimized_vectorstore.index.ntotal, 
                dimension
            )
            
            # 기존 인덱스를 IVF로 교체
            optimized_vectorstore.index = ivf_index
            
            # 7. 최적화된 벡터스토어 저장
            os.makedirs(self.optimized_path, exist_ok=True)
            optimized_vectorstore.save_local(self.optimized_path)
            logger.info(f"최적화된 벡터스토어 저장 완료: {self.optimized_path}")
            
            # 8. 벤치마크 - 최적화 후 성능
            logger.info("\n--- 최적화된 벡터스토어 성능 테스트 ---")
            
            # 최적화된 벡터스토어 다시 로드
            optimized_vectorstore = FAISS.load_local(
                self.optimized_path,
                embeddings,
                allow_dangerous_deserialization=True
            )
            
            for query in test_queries:
                # 카테고리 기반 필터링
                category = self._classify_query(query)
                
                start_time = time.time()
                if category:
                    # 메타데이터 필터링 시뮬레이션
                    results = []
                    all_results = optimized_vectorstore.similarity_search_with_score(query, k=10)
                    for doc, score in all_results:
                        if doc.metadata.get('category') == category:
                            results.append((doc, score))
                            if len(results) >= 3:
                                break
                else:
                    results = optimized_vectorstore.similarity_search_with_score(query, k=3)
                
                elapsed = time.time() - start_time
                logger.info(f"쿼리: '{query}' (카테고리: {category}) - 소요시간: {elapsed:.3f}초")
                
                # 결과 샘플 출력
                if results:
                    logger.info(f"  최상위 결과: {results[0][0].page_content[:100]}...")
                    logger.info(f"  메타데이터: {results[0][0].metadata}")
            
            logger.info("\n=== 최적화 완료 ===")
            
            # 통계 출력
            logger.info(f"기존 벡터 수: {num_vectors}")
            logger.info(f"최적화 후 벡터 수: {optimized_vectorstore.index.ntotal}")
            logger.info(f"청크 크기: 500자")
            logger.info(f"인덱스 타입: IVF (nlist={ivf_index.nlist}, nprobe={ivf_index.nprobe})")
            
            return optimized_vectorstore
            
        except Exception as e:
            logger.error(f"최적화 실패: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _classify_query(self, query):
        """쿼리 카테고리 분류"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['운동', '스쿼트', '푸시업', '플랭크']):
            return 'exercise'
        elif any(word in query_lower for word in ['단백질', '영양', '음식', '칼로리']):
            return 'nutrition'
        elif any(word in query_lower for word in ['스트레스', '건강', '질병', '증상']):
            return 'health'
        
        return None


if __name__ == "__main__":
    optimizer = VectorstoreOptimizer()
    optimizer.optimize_vectorstore()
