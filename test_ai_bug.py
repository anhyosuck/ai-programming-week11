import pytest
from bug3_logic import find_max, count_pass


# =========================================================
# find_max 테스트
# =========================================================

# ---------- 정상 케이스 ----------
def test_find_max_normal_data():
    # 실제 사용 데이터: 최댓값 95가 리스트 마지막에 있음
    assert find_max([70, 85, 60, 95]) == 95


def test_find_max_max_in_middle():
    assert find_max([10, 99, 20]) == 99


def test_find_max_max_at_first():
    assert find_max([100, 50, 30]) == 100


def test_find_max_max_at_last():
    assert find_max([1, 2, 3]) == 3


def test_find_max_negative_numbers():
    assert find_max([-5, -2, -9]) == -2


def test_find_max_floats():
    assert find_max([59.5, 60.5, 60.0]) == 60.5


def test_find_max_all_same():
    assert find_max([80, 80, 80]) == 80


# ---------- 경계값 케이스 ----------
def test_find_max_single_element():
    # 원소가 1개인 최소 길이 리스트
    assert find_max([42]) == 42


def test_find_max_two_elements():
    # 원소가 2개이고 큰 값이 뒤에 있는 경우
    assert find_max([3, 7]) == 7


# ---------- 예외 케이스 ----------
def test_find_max_empty_list_raises():
    # 빈 리스트는 scores[0]에서 IndexError 발생
    with pytest.raises(IndexError):
        find_max([])


def test_find_max_none_raises():
    # None은 인덱싱할 수 없어서 TypeError 발생
    with pytest.raises(TypeError):
        find_max(None)


