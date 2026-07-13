# 두산 베어스 경기정보 자동 페이지

## 작동 방식

1. GitHub Actions가 10분마다 NOL 두산 페이지를 읽습니다.
2. 페이지 안의 경기 JSON을 추출합니다.
3. `games.json`을 자동 갱신합니다.
4. GitHub Pages의 `index.html`이 표로 보여줍니다.

## 최초 설정

1. 이 ZIP의 파일과 폴더를 저장소 최상위에 그대로 업로드합니다.
2. 저장소의 `Settings → Actions → General`로 이동합니다.
3. `Workflow permissions`에서 `Read and write permissions`를 선택하고 저장합니다.
4. `Actions` 탭에서 `두산 경기정보 자동 갱신`을 선택합니다.
5. `Run workflow`를 눌러 최초 1회 실행합니다.
6. 저장소의 `Settings → Pages`로 이동합니다.
7. Source를 `Deploy from a branch`로 선택합니다.
8. Branch는 `main`, 폴더는 `/(root)`로 선택하고 저장합니다.

## 참고

- 예약 실행은 10분마다 설정되어 있지만 GitHub 사정에 따라 지연될 수 있습니다.
- NOL 페이지 구조가 변경되면 추출 코드 수정이 필요할 수 있습니다.
