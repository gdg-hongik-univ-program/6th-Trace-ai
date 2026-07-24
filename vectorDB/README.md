# vectorDB — 문제 벡터DB 구축

교과서 문제 데이터를 임베딩해서 Chroma 벡터DB로 만드는 코드. 


| 파일 | 버전 | 역할 |
|---|---|---|
| `vectordb_v2.ipynb` | v2 | 벡터DB 재구축 코드 |
| `problem_data_chromadb_pipeline (1).ipynb` | v1 | 기존 벡터DB 구축 코드 |

## 문제 상황: 검색 품질

기존(v1) 파이프라인은 `learning_data_info`(문항의 원본 JSON 구조 전체)를 `str()`로 통째로 문자열화해서 `page_content`(=임베딩되는 텍스트)로 사용했다.

```python
# v1: 원본 Cell 17
df["text"] = df["learning_data_info"].astype(str)
```

그 결과 실제로 임베딩되는 텍스트가 이런 식이었다:

```
[{'class_num': 1, 'class_name': '문항(텍스트)', 'class_info_list': [{'Type': 'Bounding_Box', 'Type_value': [[12.46, 37.91, 245.71, 63.66]], ...
```

"다음 연립방정식을 풀어라"라는 20자 남짓의 의미 있는 텍스트가 `Bounding_Box`, `class_info_list`, 좌표 숫자 수십 개(OCR 레이아웃 정보)에 파묻혀서, 문서 하나당 평균 1000자가 넘는 텍스트가 만들어졌다. 의미 신호 대 잡음비가 높은 상태였고, 이 텍스트를 임베딩해서 유사도 검색을 하면 실제 문제 내용이 아니라 좌표/구조 노이즈끼리 비슷한 문서가 걸리는 문제가 있었다.

## v2에서 고친 것

`vectordb_v2.ipynb`의 3단계(전처리)에서 `class_info_list` 안에 파묻힌 텍스트 조각(`Type`, 좌표 등 잡음은 제외)만 뽑아 **문항 + 성취기준** 정도의 짧고 의미 있는 텍스트로 재구성한다.

| | 기존(v1) | v2 |
|---|---|---|
| 임베딩 텍스트 | `str(learning_data_info)` 통째로 (~1000자+) | 문항 + 성취기준만 (~100자) |
| 신호 대 잡음비 | 낮음 (좌표/구조 정보에 파묻힘) | 높음 (의미 있는 텍스트만) |

노트북 구성:

1. **설치** — 필요 패키지 설치 (Colab 기준)
2. **Drive 마운트 & 압축 해제** *(원본과 동일)*
3. **DataFrame 생성** *(원본과 동일)*
4. **전처리 ★ 핵심 변경점 ★** — `learning_data_info`에서 잡음(좌표, Type 등)을 걷어내고 문항 텍스트만 추출해 `build_record`로 적재용 dict 생성. 적재 전 반드시 **3-1. 품질 점검** 셀로 임베딩 텍스트 평균 길이(~100자대인지), 객관식 선택지 개수 등을 눈으로 확인해야 한다 — 한번 적재하면 다시 빼기 번거롭기 때문.
5. **임베딩 & 적재** — 기존과 동일한 임베딩 모델(`jhgan/ko-sroberta-multitask`)을 사용해 Chroma에 적재. **적재할 때와 검색할 때(서비스 코드, `rag/rag_pipeline.py`) 임베딩 모델이 다르면 벡터 공간이 달라져 검색 결과가 무작위에 가까워지므로 반드시 동일한 모델을 써야 한다.**
6. **검증** — 개념어로 검색했을 때 해당 단원 문제만 나오는지, 메타데이터 필터(`grade`, `difficulty`, `ptype`, `school`)가 정상 동작하는지 확인.

## 사용하는 서비스 코드와의 연결

`rag/rag_pipeline.py`는 `data/chromadb`(=이 노트북이 적재하는 경로)를 `collection_name="problem_collection"`으로 열어 `similarity_search`로 퀴즈를 검색한다. 벡터DB를 재구축할 경우 컬렉션 이름과 임베딩 모델이 서비스 코드와 일치하는지 반드시 확인할 것.
