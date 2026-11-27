from pathlib import Path
import pandas as pd

def 정제(df):
    print("시작       ", len(df))
    df = df.dropna(subset=["점수"])
    print("빈 칸 제거 ", len(df))
    df = df.drop_duplicates()
    print("중복 제거  ", len(df))
    df["반"] = df["반"].str.strip()
    df["과목"] = df["과목"].str.strip()
    df = df[(df["점수"] >= 0) & (df["점수"] <= 100)]
    print("범위 밖 제거", len(df))
    return df

def 반별평균(df):
    return df.groupby("반")["점수"].mean().round(2)


if __name__ == "__main__":
    df = pd.read_csv(Path(__file__).with_name("scores_2026.csv"))
    print("시작:", len(df), "행")
    df = 정제(df)
    print(sorted(df["반"].unique()))
    print(sorted(df["과목"].unique()))

    # B 필터링 (df를 덮어쓰지 않음)
    수학 = df[df["과목"] == "수학"]
    print("수학 과목 필터링 후:", len(수학), "행")

    # C 그룹화
    print(반별평균(df))
    print(df.groupby(["과목", "반"])["점수"].mean().round(2))

    # D 통계
    통계 = df.groupby("반")["점수"].agg(개수="count", 평균="mean", 중앙값="median", 최댓값="max").round(2)
    print(통계)

    # 검증: 합계 일치, 개수 일치, 스팟 체크
    print(df.groupby("반")["점수"].sum().sum(), df["점수"].sum())
    print(df.groupby("반")["점수"].count().sum(), len(df))
    print(df[(df["반"] == "1반") & (df["과목"] == "수학")]["점수"].tolist())