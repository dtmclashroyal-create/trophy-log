# 트로피 기록장

클래시 로얄 랭크 점수와 트로피를 10분마다 자동으로 기록하는 핸드폰용 웹앱이에요.

- `index.html`, `manifest.webmanifest`, `sw.js`, `icon*`: 앱 화면 (GitHub Pages로 배포)
- `data/battles.json`: 쌓인 경기 기록
- `scripts/sync.py`: 공식 API(RoyaleAPI 프록시 경유)에서 배틀 로그를 가져와 합치는 스크립트
- `.github/workflows/sync.yml`: 10분마다 위 스크립트를 실행하고 바뀐 기록을 커밋

## 설정

1. 저장소 **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `CR_API_KEY`, Secret: developer.clashroyale.com에서 만든 키 (허용 IP `45.79.218.79`)
2. (선택) 같은 화면의 **Variables** 탭에서 `CR_TAG` = 플레이어 태그 (기본값 `222PVQCR8`)
3. **Settings → Pages**: Source를 `Deploy from a branch`, Branch를 `main` / `/ (root)`로 저장
4. **Actions** 탭에서 워크플로를 켜고 `배틀 기록 동기화 → Run workflow`로 한 번 실행

배틀 로그는 최근 25~30판만 남기 때문에, 10분 안에 그보다 많이 하지 않는 한 모든 경기가 기록돼요.
