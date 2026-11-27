import pytest

from load_scores import load_scores


# ─────────────────────────────────────────────
# 공통 도우미: 임시 폴더에 CSV 파일을 만들어 경로를 돌려준다
#   - tmp_path 는 pytest가 테스트마다 새로 만들어 주는 임시 폴더
#   - 테스트가 끝나면 실제 프로젝트 폴더에는 아무 파일도 남지 않는다
# ─────────────────────────────────────────────
@pytest.fixture
def make_csv(tmp_path):
    def _make(text, encoding="utf-8"):
        path = tmp_path / "scores.csv"
        path.write_text(text, encoding=encoding)
        return path
    return _make


# =============================================
# 1. 정상 케이스
# =============================================

def test_normal_valid_rows(make_csv):
    """올바른 데이터는 모두 kept 에 들어가고 skipped 는 비어 있다."""
    path = make_csv("이름,점수\n홍길동,90\n김철수,75\n")
    kept, skipped = load_scores(path)
    assert kept == [("홍길동", 90), ("김철수", 75)]
    assert skipped == []


def test_normal_strip_spaces(make_csv):
    """이름과 점수 앞뒤 공백은 제거된다."""
    path = make_csv("이름,점수\n  홍길동  ,  90  \n")
    kept, skipped = load_scores(path)
    assert kept == [("홍길동", 90)]
    assert skipped == []


def test_normal_header_is_always_skipped(make_csv):
    """첫 줄은 내용과 상관없이 헤더로 보고 건너뛴다."""
    path = make_csv("홍길동,90\n김철수,80\n")
    kept, skipped = load_scores(path)
    assert kept == [("김철수", 80)]
    assert skipped == []


def test_normal_blank_line_not_recorded(make_csv):
    """빈 줄은 kept 에도 skipped 에도 들어가지 않는다."""
    path = make_csv("이름,점수\n\n홍길동,90\n\n")
    kept, skipped = load_scores(path)
    assert kept == [("홍길동", 90)]
    assert skipped == []


def test_normal_blank_line_counts_in_line_number(make_csv):
    """빈 줄도 줄 번호 계산에는 포함된다. (1행 헤더, 2행 빈 줄, 3행 오류)"""
    path = make_csv("이름,점수\n\n홍길동,abc\n")
    kept, skipped = load_scores(path)
    assert kept == []
    assert skipped == [(3, "홍길동,abc", "점수가 정수가 아님")]


def test_normal_utf8_bom(make_csv):
    """BOM 이 붙은 UTF-8 파일(엑셀에서 저장한 CSV 등)도 읽을 수 있다."""
    path = make_csv("이름,점수\n홍길동,90\n", encoding="utf-8-sig")
    kept, skipped = load_scores(path)
    assert kept == [("홍길동", 90)]
    assert skipped == []


def test_normal_crlf_line_endings(tmp_path):
    """Windows 줄바꿈(\\r\\n)으로 저장된 파일도 읽을 수 있다."""
    path = tmp_path / "scores.csv"
    path.write_bytes("이름,점수\r\n홍길동,90\r\n".encode("utf-8"))
    kept, skipped = load_scores(path)
    assert kept == [("홍길동", 90)]
    assert skipped == []


def test_normal_no_trailing_newline(make_csv):
    """마지막 줄 끝에 줄바꿈이 없어도 읽힌다."""
    path = make_csv("이름,점수\n홍길동,90")
    kept, skipped = load_scores(path)
    assert kept == [("홍길동", 90)]


def test_normal_quoted_name_with_comma(make_csv):
    """큰따옴표로 감싼 이름 안의 쉼표는 열 구분자로 보지 않는다."""
    path = make_csv('이름,점수\n"홍,길동",90\n')
    kept, skipped = load_scores(path)
    assert kept == [("홍,길동", 90)]
    assert skipped == []


def test_normal_return_type(make_csv):
    """반환값은 (list, list) 형태의 튜플이다."""
    path = make_csv("이름,점수\n홍길동,90\n")
    result = load_scores(path)
    assert isinstance(result, tuple)
    assert len(result) == 2
    kept, skipped = result
    assert isinstance(kept, list)
    assert isinstance(skipped, list)


# =============================================
# 2. 예외 케이스 (잘못된 줄은 skipped 에 기록)
# =============================================

def test_error_one_column(make_csv):
    path = make_csv("이름,점수\n홍길동\n")
    kept, skipped = load_scores(path)
    assert kept == []
    assert skipped == [(2, "홍길동", "열 개수가 2가 아님")]


def test_error_three_columns(make_csv):
    path = make_csv("이름,점수\n홍길동,90,추가\n")
    kept, skipped = load_scores(path)
    assert kept == []
    assert skipped == [(2, "홍길동,90,추가", "열 개수가 2가 아님")]


def test_error_spaces_only_line(make_csv):
    """공백만 있는 줄은 빈 줄이 아니라 열 1개짜리 줄로 처리된다."""
    path = make_csv("이름,점수\n   \n")
    kept, skipped = load_scores(path)
    assert kept == []
    assert skipped == [(2, "   ", "열 개수가 2가 아님")]


def test_error_empty_name(make_csv):
    path = make_csv("이름,점수\n,90\n")
    kept, skipped = load_scores(path)
    assert kept == []
    assert skipped == [(2, ",90", "이름이 비어 있음")]


def test_error_name_only_spaces(make_csv):
    """이름이 공백뿐이면 strip 후 빈 문자열이 되므로 오류. 원본은 공백을 그대로 유지한다."""
    path = make_csv("이름,점수\n   ,90\n")
    kept, skipped = load_scores(path)
    assert kept == []
    assert skipped == [(2, "   ,90", "이름이 비어 있음")]


def test_error_empty_score(make_csv):
    path = make_csv("이름,점수\n홍길동,\n")
    kept, skipped = load_scores(path)
    assert kept == []
    assert skipped == [(2, "홍길동,", "점수가 비어 있음")]


def test_error_name_checked_before_score(make_csv):
    """이름과 점수가 모두 비어 있으면 이름 검사가 먼저 걸린다."""
    path = make_csv("이름,점수\n,\n")
    kept, skipped = load_scores(path)
    assert skipped == [(2, ",", "이름이 비어 있음")]


@pytest.mark.parametrize("raw", ["abc", "90.5", "9 0", "구십", "1e2"])
def test_error_score_not_integer(make_csv, raw):
    path = make_csv(f"이름,점수\n홍길동,{raw}\n")
    kept, skipped = load_scores(path)
    assert kept == []
    assert skipped == [(2, f"홍길동,{raw}", "점수가 정수가 아님")]


def test_error_file_not_found(tmp_path):
    """존재하지 않는 파일이면 FileNotFoundError 가 발생한다."""
    with pytest.raises(FileNotFoundError):
        load_scores(tmp_path / "없는파일.csv")


def test_error_mixed_file(make_csv):
    """정상 줄과 여러 종류의 오류 줄이 섞인 파일 전체 검증."""
    text = (
        "이름,점수\n"      # 1행 헤더
        "홍길동,90\n"      # 2행 정상
        "\n"               # 3행 빈 줄 (기록 안 함)
        "김철수\n"         # 4행 열 개수 오류
        ",80\n"            # 5행 이름 없음
        "이영희,\n"        # 6행 점수 없음
        "박민수,abc\n"     # 7행 정수 아님
        "최지우,101\n"     # 8행 범위 밖
        "정우성,100\n"     # 9행 정상
    )
    path = make_csv(text)
    kept, skipped = load_scores(path)
    assert kept == [("홍길동", 90), ("정우성", 100)]
    assert skipped == [
        (4, "김철수", "열 개수가 2가 아님"),
        (5, ",80", "이름이 비어 있음"),
        (6, "이영희,", "점수가 비어 있음"),
        (7, "박민수,abc", "점수가 정수가 아님"),
        (8, "최지우,101", "점수가 0~100 밖"),
    ]


# =============================================
# 3. 경계값 케이스
# =============================================

@pytest.mark.parametrize(
    "raw, expected",
    [
        ("0", 0),       # 최솟값
        ("1", 1),       # 최솟값 바로 위
        ("99", 99),     # 최댓값 바로 아래
        ("100", 100),   # 최댓값
        ("-0", 0),      # int("-0") 은 0 이므로 허용
        ("+100", 100),  # int("+100") 은 100 이므로 허용
        ("007", 7),     # 앞의 0 은 무시됨
    ],
)
def test_boundary_inside_range(make_csv, raw, expected):
    path = make_csv(f"이름,점수\n홍길동,{raw}\n")
    kept, skipped = load_scores(path)
    assert kept == [("홍길동", expected)]
    assert skipped == []


@pytest.mark.parametrize("raw", ["-1", "101", "-100", "1000"])
def test_boundary_outside_range(make_csv, raw):
    path = make_csv(f"이름,점수\n홍길동,{raw}\n")
    kept, skipped = load_scores(path)
    assert kept == []
    assert skipped == [(2, f"홍길동,{raw}", "점수가 0~100 밖")]


def test_boundary_empty_file(make_csv):
    """완전히 빈 파일이면 둘 다 빈 리스트."""
    path = make_csv("")
    assert load_scores(path) == ([], [])


def test_boundary_header_only(make_csv):
    """헤더만 있으면 둘 다 빈 리스트."""
    path = make_csv("이름,점수\n")
    assert load_scores(path) == ([], [])


def test_boundary_single_char_name(make_csv):
    """한 글자 이름도 정상 처리된다."""
    path = make_csv("이름,점수\n김,50\n")
    kept, skipped = load_scores(path)
    assert kept == [("김", 50)]