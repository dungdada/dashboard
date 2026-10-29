# kr-claims

- `data/` 의 원본은 수정 금지. 가공은 `build.py` 로만 하고 결과는 `data/data.json` 에 쓴다.
- 화면 내용(지표·차트)은 `config.json` 이 단일 출처. 코드에 하드코딩하지 않는다.
- 코드 컬럼은 문자열로 유지한다 (앞자리 0 보존).
- 결정과 인터뷰 답변은 `interview.md` 에 날짜와 함께 남긴다.
- 외부 라이브러리는 CDN, 버전 고정. 빌드 도구 없이 정적 파일로 동작해야 한다.
- 실행: `python build.py` 후 `python -m http.server 8000`, `http://localhost:8000/`
- 파일이 커지면 분리 (index.html 300줄 → css/js, build.py 200줄 → scripts/).
