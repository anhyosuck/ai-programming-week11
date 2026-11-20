import pytest

from load_scores import load_scores


@pytest.fixture
def make_csv(tmp_path):
    """테스트마다 임시 CSV 파일을 만드는 도우미."""
    def _make_csv(content, filename="scores.csv"):
        path = tmp_path / filename
        path.write_bytes(content.encode("utf-8"))
        return path

    return _make_csv


# ============================================================
# 1. 정상 입력
# ============================================================

def test_load_normal_scores(make_csv):
    path = make_csv(
        "name,score\n"
        "민수,90\n"
        "지영,85.5\n"
        "수빈,100\n"
    )

    records, skipped_lines = load_scores(path)

    assert records == [
        ("민수", 90.0),
        ("지영", 85.5),
        ("수빈", 100.0),
    ]
    assert skipped_lines == []


@pytest.mark.parametrize("use_string_path", [False, True])
def test_accepts_path_object_and_string(make_csv, use_string_path):
    path = make_csv("name,score\n민수,90\n")
    argument = str(path) if use_string_path else path

    assert load_scores(argument) == ([("민수", 90.0)], [])


def test_strips_whitespace_from_name_and_score(make_csv):
    path = make_csv(
        "name,score\n"
        "  민수  , 90.5 \n"
    )

    assert load_scores(path) == ([("민수", 90.5)], [])


def test_reads_quoted_name_containing_comma(make_csv):
    path = make_csv(
        "name,score\n"
        '"Kim, Minsoo",90\n'
    )

    assert load_scores(path) == ([("Kim, Minsoo", 90.0)], [])


def test_reads_file_without_final_newline(make_csv):
    path = make_csv("name,score\n민수,90")

    assert load_scores(path) == ([("민수", 90.0)], [])


def test_reads_windows_line_endings(make_csv):
    path = make_csv(
        "name,score\r\n"
        "민수,90\r\n"
        "지영,80\r\n"
    )

    assert load_scores(path) == (
        [("민수", 90.0), ("지영", 80.0)],
        [],
    )


# ============================================================
# 2. 파일 및 헤더 예외
# ============================================================

def test_missing_file_raises_file_not_found_error(tmp_path):
    path = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError):
        load_scores(path)

    # 없는 파일을 새로 만들면 안 됩니다.
    assert not path.exists()


@pytest.mark.parametrize(
    "content",
    [
        "",                         # 완전히 빈 파일
        "\n",                       # 빈 첫 줄
        "민수,90\n",                # 헤더 없음
        "student,score\n",           # 잘못된 헤더 이름
        "name,point\n",              # 잘못된 헤더 이름
        "score,name\n",              # 잘못된 헤더 순서
        "name\n",                   # 헤더 열 부족
        "name,score,extra\n",        # 헤더 열 초과
    ],
)
def test_invalid_header_raises_value_error(make_csv, content):
    path = make_csv(content)

    with pytest.raises(ValueError):
        load_scores(path)


# ============================================================
# 3. 점수 경계값
# ============================================================

@pytest.mark.parametrize(
    ("score_text", "expected_score"),
    [
        ("0", 0.0),
        ("100", 100.0),
        ("0.001", 0.001),
        ("99.999", 99.999),
    ],
)
def test_accepts_scores_inside_inclusive_range(
    make_csv, score_text, expected_score
):
    path = make_csv(f"name,score\n민수,{score_text}\n")

    records, skipped_lines = load_scores(path)

    assert len(records) == 1
    assert records[0][0] == "민수"
    assert records[0][1] == pytest.approx(expected_score)
    assert skipped_lines == []


# ============================================================
# 4. 잘못된 데이터 행
# ============================================================

@pytest.mark.parametrize(
    "invalid_row",
    [
        "민수,-0.001",        # 최솟값 바로 아래
        "민수,100.001",       # 최댓값 바로 위
        "민수,-1",           # 음수
        "민수,101",          # 범위 초과
        "민수,abc",          # 숫자가 아닌 점수
        "민수,",             # 빈 점수
        "민수,   ",          # 공백뿐인 점수
        "민수,nan",          # NaN
        "민수,inf",          # 양의 무한대
        "민수,-inf",         # 음의 무한대
        "민수",              # 열 부족
        "민수,90,extra",     # 열 초과
        ",90",               # 빈 이름
        "   ,90",            # 공백뿐인 이름
        "",                  # 빈 줄
    ],
)
def test_skips_invalid_row_and_continues(make_csv, invalid_row):
    path = make_csv(
        "name,score\n"
        f"{invalid_row}\n"
        "정상학생,80\n"
    )

    records, skipped_lines = load_scores(path)

    assert records == [("정상학생", 80.0)]
    assert skipped_lines == [2]


def test_records_all_skipped_line_numbers_in_order(make_csv):
    path = make_csv(
        "name,score\n"       # 1
        "민수,90\n"          # 2: 정상
        "지영,abc\n"         # 3: 숫자가 아님
        "\n"                 # 4: 빈 줄
        "수빈,101\n"         # 5: 범위 초과
        "하늘,80\n"          # 6: 정상
        "민수,95\n"          # 7: 중복 이름
        "유진,70,extra\n"    # 8: 열 초과
        "지우,\n"            # 9: 빈 점수
    )

    records, skipped_lines = load_scores(path)

    assert records == [
        ("민수", 90.0),
        ("하늘", 80.0),
    ]
    assert skipped_lines == [3, 4, 5, 7, 8, 9]


# ============================================================
# 5. 중복 이름
# ============================================================

def test_duplicate_name_keeps_first_valid_record(make_csv):
    path = make_csv(
        "name,score\n"
        "민수,90\n"
        "민수,95\n"
    )

    assert load_scores(path) == ([("민수", 90.0)], [3])


def test_duplicate_name_is_checked_after_stripping(make_csv):
    path = make_csv(
        "name,score\n"
        "민수,90\n"
        "  민수  ,95\n"
    )

    assert load_scores(path) == ([("민수", 90.0)], [3])


def test_invalid_record_does_not_reserve_name(make_csv):
    path = make_csv(
        "name,score\n"
        "민수,abc\n"
        "민수,90\n"
    )

    # 첫 행은 점수가 잘못되어 등록되지 않았으므로,
    # 다음 정상 행을 중복으로 처리하면 안 됩니다.
    assert load_scores(path) == ([("민수", 90.0)], [2])


# ============================================================
# 6. 데이터가 없는 경우
# ============================================================

def test_header_only_returns_empty_lists(make_csv):
    path = make_csv("name,score\n")

    assert load_scores(path) == ([], [])


def test_all_invalid_rows_return_empty_records(make_csv):
    path = make_csv(
        "name,score\n"
        "민수,-1\n"
        "지영,\n"
        "수빈,abc\n"
    )

    assert load_scores(path) == ([], [2, 3, 4])


# ============================================================
# 7. 원본 파일 보존
# ============================================================

@pytest.mark.parametrize(
    ("content", "raises_error"),
    [
        (
            "name,score\n민수,90\n지영,abc\n민수,95\n",
            False,
        ),
        (
            "wrong,header\n민수,90\n",
            True,
        ),
    ],
)
def test_does_not_modify_source_file(make_csv, content, raises_error):
    path = make_csv(content)
    original_bytes = path.read_bytes()

    if raises_error:
        with pytest.raises(ValueError):
            load_scores(path)
    else:
        load_scores(path)

    assert path.read_bytes() == original_bytes