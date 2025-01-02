# stock.py

import pygame
import random
import sys
import uuid
import string
import math
import Message  # Message.py가 동일한 디렉토리에 있어야 합니다.
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, filename='simulation.log',
                    format='%(asctime)s - %(levelname)s - %(message)s')

# ############################
# 2) 회사/마켓/투자자 정의
# ############################

class Company:
    def __init__(self, name, sector, initial_price):
        self.id = str(uuid.uuid4())
        self.name = name
        self.sector = sector
        self.is_bankrupt = False
        self.bankrupt_day = None
        self.bankruptcy_warning_days = 0.0

        # 뉴스 관련 변수 추가
        self.news_impact = 0.0  # 뉴스로 인한 추가 변동률
        self.news_impact_days = 0  # 뉴스 영향 지속 일수

        # 초기 주가 설정
        self.candles = [{
            "open": initial_price,
            "high": initial_price,
            "low": initial_price,
            "close": initial_price
        }]
        self.capital = random.randint(5000000, 10000000)
        self.debt = random.randint(1000, 5000000)

        # 추가된 재무 정보
        self.revenue = random.uniform(1000000, 5000000)  # 매출
        self.net_income = random.uniform(-500000, 500000)  # 순이익
        self.market_share = random.uniform(1.0, 10.0)  # 시장 점유율 (%)
        self.competitors = []  # 경쟁사 목록

    @property
    def current_price(self):
        """현재 주가 반환"""
        return self.candles[-1]["close"] if self.candles else 0

    def update_price_daily(self, econ_factor=1.0, economic_factors=None, national_factors=None):
        if self.is_bankrupt:
            return

        MAX_PRICE = 30000000
        prev_close = self.current_price

        # 기본 변동성 축소
        base_volatility = econ_factor * random.uniform(0.00005, 0.00025)  # 절반으로 축소
        trend_factor = 1 + random.uniform(-0.00025, 0.00025)  # 절반으로 축소

        # 뉴스로 인한 추가 변동 적용
        news_impact = self.apply_news_impact()
        trend_factor += news_impact

        # 경제 요인 및 국가 요인 적용
        price_adjustment = 1.0
        if economic_factors:
            price_adjustment += 0.00005 * economic_factors.get('gdp_growth', 2.0)
            price_adjustment -= 0.00005 * economic_factors.get('inflation', 2.0)
            price_adjustment -= 0.00002 * economic_factors.get('interest_rate', 1.5)
            price_adjustment -= 0.00005 * economic_factors.get('unemployment', 1.0)
        if national_factors:
            # 국가 요인이 주가에 미치는 영향 (예시로 총 자산, 출산율, 인구 추가)
            price_adjustment += 0.00003 * national_factors.get('total_assets', 23000.0)
            price_adjustment += 0.00002 * national_factors.get('birth_rate', 1.5)
            price_adjustment += 0.00001 * national_factors.get('population', 1000000)

        # 가격 변동 계산
        change_factor = random.uniform(-base_volatility, base_volatility)
        open_price = prev_close * trend_factor
        high_price = open_price * (1 + random.uniform(0, base_volatility))
        low_price = open_price * (1 - random.uniform(0, base_volatility))
        close_price = open_price * (1 + change_factor * price_adjustment)

        # 가격 제한 적용
        high_price = min(high_price, MAX_PRICE)
        low_price = max(low_price, 0)
        close_price = max(min(close_price, MAX_PRICE), 0)

        if high_price < low_price:
            high_price, low_price = low_price, high_price

        self.candles.append({
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price
        })

        price_change = (close_price - prev_close) / prev_close if prev_close != 0 else 0
        capital_change = self.capital * price_change / random.uniform(1.0, 1.5)  # 영향 감소
        self.capital += capital_change

        # 자본이 음수가 되지 않도록 제한
        if self.capital < 0:
            self.capital = 0

        debt_change = self.debt * -1 * price_change / random.uniform(0.5, 0.8)
        self.debt += debt_change
        if self.debt < 0:
            self.debt = 0

        # 재무 정보 업데이트 (매출과 순이익)
        self.revenue += random.uniform(-50000, 50000)  # 매출 변동
        self.revenue = max(100000, self.revenue)  # 최소 매출 제한

        self.net_income += random.uniform(-50000, 50000)  # 순이익 변동
        # 순이익이 음수가 될 수도 있음

    def check_bankruptcy(self, econ_factor=1.0, current_day=0):
        debt_ratio = self.debt / max(self.capital, 1)  # 자본이 0일 경우 방지
        high_price_threshold = 70000  # 주가가 높다고 판단하는 기준
        high_debt_threshold = 2.0  # 부채 비율이 높은 기준 (완화)

        # 주가가 낮으면 파산 경고일수 증가
        if self.current_price < 10000:  # 낮은 주가 기준
            self.bankruptcy_warning_days += 0.7  # 더 빠르게 경고일수 증가
        elif debt_ratio > high_debt_threshold:
            if self.current_price > high_price_threshold:
                self.bankruptcy_warning_days += 0.2  # 주가가 높으면 증가량 감소
            else:
                self.bankruptcy_warning_days += 0.5
        else:
            self.bankruptcy_warning_days = 0  # 부채가 안정되면 초기화

        # 파산 조건 확인
        if self.bankruptcy_warning_days >= 10 or self.capital < 500:
            self.is_bankrupt = True
            self.bankrupt_day = current_day

    def apply_news_impact(self):
        """뉴스 효과를 점진적으로 적용"""
        if self.news_impact_days > 0:
            self.news_impact_days -= 1  # 영향 일수 감소
            return self.news_impact * 0.5  # 점진적으로 완화
        return 0.0

    def get_last_diff_pct(self):
        """전일 대비 종가 변동(%)"""
        if len(self.candles) < 2:
            return 0
        oldp = self.candles[-2]["close"]
        newp = self.candles[-1]["close"]
        if oldp == 0:
            return 0
        return ((newp - oldp) / oldp) * 100

class Market:
    REMOVE_AFTER_DAYS = 7  # 파산 후 제거할 일수

    def __init__(self):
        self.companies = []
        self.bankrupt_companies = []  # 파산한 회사를 저장할 리스트 추가
        self.all_messages = []
        self.recent_messages = []
        self.day_count = 0

        self.policy_sentiment_score = 0
        self.economic_condition_list = ["호황(boom)", "보통(normal)", "불황(recession)", "위기(crisis)"]
        self.economic_condition_factor_map = [0.8, 1.0, 1.2, 1.5]

        # 정세 변동을 위한 변수 추가
        self.sentiment_amplitude = 20  # 정세 변동 폭
        self.sentiment_frequency = 0.1  # 정세 변동 주기 (주기 = 1/frequency)
        self.sentiment_phase = 0  # 정세 변동 위상

        # 회사 생성 확률 매핑 추가
        self.company_creation_prob_map = {
            "호황(boom)": 0.05,
            "보통(normal)": 0.02,
            "불황(recession)": 0.01,
            "위기(crisis)": 0.0
        }

        # 경제적 요인 초기화 (수정됨)
        self.economic_factors = {
            "gdp_growth": 2.0,
            "inflation": 2.0,
            "interest_rate": 1.5,
            "unemployment": 1.0,
            "exchange_rate": 1300.0,  # 초기 환율 (1달러 = 1300원)
            "raw_material_cost": 100.0,  # 원자재 비용
            "political_stability": 1.0,  # 정치적 안정성 (0.0 ~ 2.0)
            "innovation_index": 1.0  # 기술 혁신 지수 (0.0 ~ 2.0)
        }

        # 국가 요인 추가
        self.national_factors = {
            "total_assets": 23000.0,      # 국가의 총 자산 (예시 단위)
            "birth_rate": 1.5,           # 출산율 (예: 1.5명)
            "population": 50000000       # 인구 수 (예: 5천만 명)
        }

        # 타임프레임 설정 (타임프레임은 차트 표시 용도로만 사용)
        self.timeframes = {
            "하루": {"group_size": 1},
            "일주일": {"group_size": 7},
            "한달": {"group_size": 30},
            "1년": {"group_size": 360}
        }
        self.current_timeframe = "일주일"  # 초기 타임프레임 설정

        self.time_since_last_update = 0.0  # 주가 업데이트 간격 추적

    def stock_surge_event(self):
        candidates = [c for c in self.companies if not c.is_bankrupt and c.current_price < 50000]
        if not candidates:
            return

        target = random.choice(candidates)
        reason = random.choice(Message.POSITIVE_MESSAGES_BY_SECTOR.get(target.sector, ["이유 불명"]))

        MAX_PRICE = 300000
        target_price = min(target.current_price * random.uniform(1.03, 1.05), MAX_PRICE)
        surge_days = random.randint(5, 10)
        daily_increment = (target_price - target.current_price) / surge_days
        volatility_factor = 0.05

        target.is_surging = True
        target.surge_days_remaining = surge_days
        target.target_price = target_price
        target.daily_increment = daily_increment
        target.volatility_factor = volatility_factor

        msg = {
            "type": "surge",
            "sector": target.sector,
            "company": target.name,
            "text": f"[주가 상승] {target.name}가 {reason}으로 인해 주가 상승 예정!"
        }
        self.all_messages.append(msg)
        self.recent_messages.append(msg)

    def invest_in_company(self, c1, c2):
        """투자 처리"""
        investment_amount = random.randint(50000, 500000)

        # 투자금 이전
        c1.capital -= investment_amount
        c2.capital += investment_amount

        # 투자 수익 반영
        profit_factor = random.uniform(0.9, 1.2)  # 수익 또는 손실
        c1.capital += investment_amount * profit_factor

        # 자본이 음수가 되지 않도록 제한
        if c1.capital < 0:
            c1.capital = 0

        # 부채 변화 적용
        debt_change = c2.debt * random.uniform(-0.05, 0.05)
        c2.debt += debt_change
        if c2.debt < 0:
            c2.debt = 0

        # 뉴스 메시지 추가
        msg = {
            "type": "investment",
            "sector": c1.sector,
            "company": f"{c1.name} -> {c2.name}",
            "text": f"[투자] {c1.name}가 {c2.name}에 {investment_amount:,}원을 투자"
        }
        self.all_messages.append(msg)
        self.recent_messages.append(msg)

    def acquire_shares(self, c1, c2):
        """지분 인수"""
        share_percentage = random.uniform(10, 30)  # 10~30% 지분 인수
        acquisition_cost = c2.capital * (share_percentage / 100)

        # 자본 조정
        c1.capital -= acquisition_cost
        c2.capital += acquisition_cost * 0.9  # 인수된 회사에 일부 유입
        c2.debt -= acquisition_cost * 0.1  # 부채 감소

        # 자본이 음수가 되지 않도록 제한
        if c1.capital < 0:
            c1.capital = 0
        if c2.debt < 0:
            c2.debt = 0

        # 뉴스 메시지 추가
        msg = {
            "type": "acquisition",
            "sector": c1.sector,
            "company": f"{c1.name} -> {c2.name}",
            "text": f"[지분 인수] {c1.name}가 {c2.name}의 {share_percentage:.1f}% 지분을 인수"
        }
        self.all_messages.append(msg)
        self.recent_messages.append(msg)

    def create_merged_name(self, c1, c2):
        """합병 회사 이름 생성"""
        # 두 회사 이름의 첫 글자만 조합하거나 새 랜덤 이름 생성
        if random.random() < 0.7:  # 70% 확률로 기존 이름 조합
            name_part1 = c1.name[:2]  # 첫 번째 회사 이름의 앞 2글자
            name_part2 = c2.name[:2]  # 두 번째 회사 이름의 앞 2글자
            return f"{name_part1}{name_part2}"  # 조합된 이름 반환
        else:  # 30% 확률로 완전히 새 이름 생성
            return random_company_name()

    def transfer_holdings_to_merged_company(self, c1, c2, new_company, investors):
        """합병 후 투자자 주식 처리"""
        for investor in investors:
            # 기존 회사 주식 보유 여부 확인
            h1 = investor.holdings.get(c1.id, {"quantity": 0, "avg_price": 0})
            h2 = investor.holdings.get(c2.id, {"quantity": 0, "avg_price": 0})

            # 합병 후 주식 수량 및 평균 단가 계산
            new_quantity = h1["quantity"] + h2["quantity"]
            if new_quantity > 0:
                total_cost = (h1["quantity"] * h1["avg_price"]) + (h2["quantity"] * h2["avg_price"])
                new_avg_price = total_cost / new_quantity
            else:
                new_avg_price = 0

            # 새 회사로 주식 이전
            if new_quantity > 0:
                investor.holdings[new_company.id] = {"quantity": new_quantity, "avg_price": new_avg_price}

            # 기존 회사 주식 제거
            if c1.id in investor.holdings:
                del investor.holdings[c1.id]
            if c2.id in investor.holdings:
                del investor.holdings[c2.id]

    def merge_or_partner(self, c1, c2, investors):
        """두 회사의 합병 또는 제휴 처리"""
        if random.random() < 0.5:  # 50% 확률로 합병
            # 새로운 회사 이름 생성
            merged_name = self.create_merged_name(c1, c2)
            merged_sector = c1.sector if random.random() < 0.5 else c2.sector
            merged_price = (c1.current_price + c2.current_price) / 2
            merged_capital = c1.capital + c2.capital
            merged_debt = c1.debt + c2.debt

            # 새 회사 생성
            new_company = Company(merged_name, merged_sector, merged_price)
            new_company.capital = merged_capital
            new_company.debt = merged_debt
            self.add_company(new_company)

            # 투자자 주식 처리
            self.transfer_holdings_to_merged_company(c1, c2, new_company, investors)

            # 기존 회사 제거
            self.companies.remove(c1)
            self.companies.remove(c2)

            # 뉴스 메시지 추가
            msg = {
                "type": "merge",
                "sector": merged_sector,
                "company": merged_name,
                "text": f"[합병] {c1.name}와 {c2.name}가 합병하여 {merged_name}로 새롭게 출범"
            }
            self.all_messages.append(msg)
            self.recent_messages.append(msg)

        else:  # 제휴 처리
            # 자본 및 부채 공유 (제휴 효과 적용)
            c1.capital += c2.capital * 0.1
            c2.capital += c1.capital * 0.1
            c1.debt += c2.debt * 0.1
            c2.debt += c1.debt * 0.1

            # 자본이 음수가 되지 않도록 제한
            if c1.capital < 0:
                c1.capital = 0
            if c2.capital < 0:
                c2.capital = 0
            if c1.debt < 0:
                c1.debt = 0
            if c2.debt < 0:
                c2.debt = 0

            # 주가 변동 반영
            c1_candles = c1.candles[-1]
            c2_candles = c2.candles[-1]
            c1_candles["close"] *= 1.05  # 5% 상승
            c2_candles["close"] *= 1.05

            # 주가가 높은지 낮은지 확인하여 파산 여부 재검토
            c1.check_bankruptcy(econ_factor=self.economic_factor, current_day=self.day_count)
            c2.check_bankruptcy(econ_factor=self.economic_factor, current_day=self.day_count)

            # 뉴스 메시지 추가
            msg = {
                "type": "partner",
                "sector": c1.sector,
                "company": f"{c1.name}-{c2.name}",
                "text": f"[제휴] {c1.name}와 {c2.name}가 전략적 제휴 체결"
            }
            self.all_messages.append(msg)
            self.recent_messages.append(msg)

    def add_random_companies(self, num):
        sector_list = ["IT", "의약", "화학", "게임", "에너지", "금융"]
        for _ in range(num):
            name = random_company_name()
            sector = random.choice(sector_list)
            price = random.uniform(5000, 40000)  # 초기 가격 완화
            new_company = Company(name, sector, price)
            # 경쟁사 추가 (예시로 2개)
            new_company.competitors = random.sample([c.name for c in self.companies], k=min(2, len(self.companies)))
            self.add_company(new_company)
            msg = {
                "type": "new",
                "sector": new_company.sector,
                "company": new_company.name,
                "text": f"[신규 상장] {new_company.name} ({new_company.sector})"
            }
            self.all_messages.append(msg)
            self.recent_messages.append(msg)

    @property
    def economic_condition(self):
        s = self.policy_sentiment_score
        if s >= 15:
            return self.economic_condition_list[0]
        elif s >= -5:
            return self.economic_condition_list[1]
        elif s > -20:
            return self.economic_condition_list[2]
        else:
            return self.economic_condition_list[3]

    @property
    def economic_factor(self):
        idx = self.economic_condition_list.index(self.economic_condition)
        return self.economic_condition_factor_map[idx]

    def add_company(self, company):
        self.companies.append(company)

    def update_sentiment(self):
        # 사인 함수를 이용한 정세 변동
        self.sentiment_phase += self.sentiment_frequency
        self.policy_sentiment_score = self.sentiment_amplitude * math.sin(self.sentiment_phase)

    def update_economic_factors(self):
        """경제적 요인 업데이트"""
        # GDP 및 기본 경제 지표 업데이트
        if self.policy_sentiment_score >= 15 :
            self.economic_factors["gdp_growth"] += random.uniform(0.5, 1.0)  # 축소된 변동
            self.economic_factors["gdp_growth"] = max(-5.0, min(self.economic_factors["gdp_growth"], 10.0))

            self.economic_factors["inflation"] += random.uniform(-0.5, -0.25)  # 축소된 변동
            self.economic_factors["inflation"] = max(-15.0, min(self.economic_factors["inflation"], 15.0))

            self.economic_factors["interest_rate"] += random.uniform(-0.1, -0.05)  # 축소된 변동
            self.economic_factors["interest_rate"] = max(0.5, min(self.economic_factors["interest_rate"], 15.0))

            self.economic_factors["unemployment"] += random.uniform(-0.15, -0.05)  # 축소된 변동
            self.economic_factors["unemployment"] = max(0.0, min(self.economic_factors["unemployment"], 7.0))

            self.economic_factors["exchange_rate"] += random.uniform(-3, -1)  # 축소된 변동
            self.economic_factors["exchange_rate"] = max(1000, min(self.economic_factors["exchange_rate"], 1500))

            self.economic_factors["raw_material_cost"] += random.uniform(-5, -2.5)  # 축소된 변동
            self.economic_factors["raw_material_cost"] = max(50, min(self.economic_factors["raw_material_cost"], 200))

            self.economic_factors["political_stability"] += random.uniform(0.0, 0.075)  # 축소된 변동
            self.economic_factors["political_stability"] = max(0.0, min(self.economic_factors["political_stability"], 2.0))

            self.economic_factors["innovation_index"] += random.uniform(0.0, 0.075)  # 축소된 변동
            self.economic_factors["innovation_index"] = max(0.0, min(self.economic_factors["innovation_index"], 2.0))

            self.national_factors["total_assets"] += random.uniform(-5, -2.5)  # 축소된 변동
            self.national_factors["total_assets"] = max(18000.0, min(self.national_factors["total_assets"], 28000.0))

            self.national_factors["birth_rate"] += random.uniform(-0.1, -0.05)  # 축소된 변동
            self.national_factors["birth_rate"] = max(0.5, min(self.national_factors["birth_rate"], 3.0))

            self.national_factors["population"] += random.randint(-5000, -2500)  # 축소된 변동
            self.national_factors["population"] = max(10000000, min(self.national_factors["population"], 100000000))

        elif self.policy_sentiment_score >= -5:
            self.economic_factors["gdp_growth"] += random.uniform(-0.25, 0.1)  # 축소된 변동
            self.economic_factors["gdp_growth"] = max(-5.0, min(self.economic_factors["gdp_growth"], 10.0))

            self.economic_factors["inflation"] += random.uniform(-0.25, 0.25)  # 축소된 변동
            self.economic_factors["inflation"] = max(-2.0, min(self.economic_factors["inflation"], 15.0))

            self.economic_factors["interest_rate"] += random.uniform(-0.05, 0.05)  # 축소된 변동
            self.economic_factors["interest_rate"] = max(0.5, min(self.economic_factors["interest_rate"], 15.0))

            self.economic_factors["unemployment"] += random.uniform(-0.05, 0.1)  # 축소된 변동
            self.economic_factors["unemployment"] = max(0.0, min(self.economic_factors["unemployment"], 7.0))

            self.economic_factors["exchange_rate"] += random.uniform(-5, 5)  # 축소된 변동
            self.economic_factors["exchange_rate"] = max(1000, min(self.economic_factors["exchange_rate"], 1500))

            self.economic_factors["raw_material_cost"] += random.uniform(-2.5, 2.5)  # 축소된 변동
            self.economic_factors["raw_material_cost"] = max(50, min(self.economic_factors["raw_material_cost"], 200))

            self.economic_factors["political_stability"] += random.uniform(-0.025, 0.025)  # 축소된 변동
            self.economic_factors["political_stability"] = max(0.0, min(self.economic_factors["political_stability"], 2.0))

            self.economic_factors["innovation_index"] += random.uniform(-0.025, 0.025)  # 축소된 변동
            self.economic_factors["innovation_index"] = max(0.0, min(self.economic_factors["innovation_index"], 2.0))

            self.national_factors["total_assets"] += random.uniform(-2.5, 2.5)  # 축소된 변동
            self.national_factors["total_assets"] = max(18000.0, min(self.national_factors["total_assets"], 28000.0))

            self.national_factors["birth_rate"] += random.uniform(-0.05, 0.05)  # 축소된 변동
            self.national_factors["birth_rate"] = max(0.5, min(self.national_factors["birth_rate"], 3.0))

            self.national_factors["population"] += random.randint(-2500, 2500)  # 축소된 변동
            self.national_factors["population"] = max(10000000, min(self.national_factors["population"], 100000000))

        elif self.policy_sentiment_score > -20 :
            self.economic_factors["gdp_growth"] += random.uniform(-0.75, 0.05)  # 축소된 변동
            self.economic_factors["gdp_growth"] = max(-5.0, min(self.economic_factors["gdp_growth"], 10.0))

            self.economic_factors["inflation"] += random.uniform(-0.0125, 0.25)  # 축소된 변동
            self.economic_factors["inflation"] = max(-2.0, min(self.economic_factors["inflation"], 15.0))

            self.economic_factors["interest_rate"] += random.uniform(-0.025, 0.05)  # 축소된 변동
            self.economic_factors["interest_rate"] = max(0.5, min(self.economic_factors["interest_rate"], 15.0))

            self.economic_factors["unemployment"] += random.uniform(-0.025, 0.1)  # 축소된 변동
            self.economic_factors["unemployment"] = max(0.0, min(self.economic_factors["unemployment"], 7.0))

            self.economic_factors["exchange_rate"] += random.uniform(-2.5, 5)  # 축소된 변동
            self.economic_factors["exchange_rate"] = max(1000, min(self.economic_factors["exchange_rate"], 1500))

            self.economic_factors["raw_material_cost"] += random.uniform(-1.25, 2.5)  # 축소된 변동
            self.economic_factors["raw_material_cost"] = max(50, min(self.economic_factors["raw_material_cost"], 200))

            self.economic_factors["political_stability"] += random.uniform(-0.0125, 0.025)  # 축소된 변동
            self.economic_factors["political_stability"] = max(0.0, min(self.economic_factors["political_stability"], 2.0))

            self.economic_factors["innovation_index"] += random.uniform(-0.0125, 0.025)  # 축소된 변동
            self.economic_factors["innovation_index"] = max(0.0, min(self.economic_factors["innovation_index"], 2.0))

            self.national_factors["total_assets"] += random.uniform(0.0, 2.5)  # 축소된 변동
            self.national_factors["total_assets"] = max(18000.0, min(self.national_factors["total_assets"], 28000.0))

            self.economic_factors["political_stability"] += random.uniform(-0.03, -0.025)  # 축소된 변동
            self.economic_factors["political_stability"] = max(0.0, min(self.economic_factors["political_stability"], 2.0))

            self.economic_factors["innovation_index"] += random.uniform(-0.03, -0.025)  # 축소된 변동
            self.economic_factors["innovation_index"] = max(0.0, min(self.economic_factors["innovation_index"], 2.0))

            self.national_factors["birth_rate"] += random.uniform(0.0, 0.05)  # 축소된 변동
            self.national_factors["birth_rate"] = max(0.5, min(self.national_factors["birth_rate"], 3.0))

            self.national_factors["population"] += random.randint(0, 2500)  # 축소된 변동
            self.national_factors["population"] = max(10000000, min(self.national_factors["population"], 100000000))

        else :
            self.economic_factors["gdp_growth"] += random.uniform(-0.2, -0.1)  # 축소된 변동
            self.economic_factors["gdp_growth"] = max(-5.0, min(self.economic_factors["gdp_growth"], 10.0))

            self.economic_factors["inflation"] += random.uniform(0.25, 0.5)  # 축소된 변동
            self.economic_factors["inflation"] = max(-2.0, min(self.economic_factors["inflation"], 15.0))

            self.economic_factors["interest_rate"] += random.uniform(0.05, 0.1)  # 축소된 변동
            self.economic_factors["interest_rate"] = max(0.5, min(self.economic_factors["interest_rate"], 15.0))

            self.economic_factors["unemployment"] += random.uniform(0.05, 0.1)  # 축소된 변동
            self.economic_factors["unemployment"] = max(0.0, min(self.economic_factors["unemployment"], 7.0))

            self.economic_factors["exchange_rate"] += random.uniform(5, 10)  # 축소된 변동
            self.economic_factors["exchange_rate"] = max(1000, min(self.economic_factors["exchange_rate"], 1500))

            self.economic_factors["raw_material_cost"] += random.uniform(2.5, 5.0)  # 축소된 변동
            self.economic_factors["raw_material_cost"] = max(50, min(self.economic_factors["raw_material_cost"], 200))

            self.economic_factors["political_stability"] += random.uniform(0.0, -0.03)  # 축소된 변동
            self.economic_factors["political_stability"] = max(0.0, min(self.economic_factors["political_stability"], 2.0))

            self.economic_factors["innovation_index"] += random.uniform(0.0, -0.03)  # 축소된 변동
            self.economic_factors["innovation_index"] = max(0.0, min(self.economic_factors["innovation_index"], 2.0))

            self.national_factors["total_assets"] += random.uniform(2.5, 5.0)  # 축소된 변동
            self.national_factors["total_assets"] = max(18000.0, min(self.national_factors["total_assets"], 28000.0))

            self.national_factors["birth_rate"] += random.uniform(0.05, 0.1)  # 축소된 변동
            self.national_factors["birth_rate"] = max(0.5, min(self.national_factors["birth_rate"], 3.0))

            self.national_factors["population"] += random.randint(-0, 5000)  # 축소된 변동
            self.national_factors["population"] = max(10000000, min(self.national_factors["population"], 100000000))

    def handle_special_events(self):
        """특별 이벤트 발생"""
        # 특별 이벤트 로직을 여기에 추가할 수 있습니다.
        # 예: 자연재해, 정치적 사건 등
        event_chance = random.random()
        if event_chance < 0.02:  # 2% 확률로 자연재해 이벤트
            self.natural_disaster_event()
        elif event_chance < 0.04:  # 추가 2% 확률로 정치적 사건 이벤트
            self.political_event()

    def natural_disaster_event(self):
        """자연재해 이벤트"""
        affected_sector = random.choice(["에너지", "화학", "의약"])
        affected_companies = [c for c in self.companies if c.sector == affected_sector and not c.is_bankrupt]
        if not affected_companies:
            return
        target = random.choice(affected_companies)
        damage_pct = random.uniform(0.05, 0.15)  # 5% ~ 15% 피해
        self.apply_price_change(target, -damage_pct * 100)

        msg = {
            "type": "natural_disaster",
            "sector": affected_sector,
            "company": target.name,
            "text": f"[자연재해] {target.name}가 자연재해로 인해 주가가 {damage_pct*100:.2f}% 하락했습니다."
        }
        self.all_messages.append(msg)
        self.recent_messages.append(msg)

    def political_event(self):
        """정치적 사건 이벤트"""
        affected_sector = random.choice(["금융", "IT", "게임"])
        affected_companies = [c for c in self.companies if c.sector == affected_sector and not c.is_bankrupt]
        if not affected_companies:
            return
        target = random.choice(affected_companies)
        impact_pct = random.uniform(-0.1, 0.1)  # -10% ~ +10% 영향
        self.apply_price_change(target, impact_pct * 100)

        event_type = "긍정적인" if impact_pct > 0 else "부정적인"
        msg = {
            "type": "political_event",
            "sector": affected_sector,
            "company": target.name,
            "text": f"[정치적 사건] {target.name}가 {event_type} 정치적 사건으로 인해 주가가 {impact_pct*100:.2f}% 변동했습니다."
        }
        self.all_messages.append(msg)
        self.recent_messages.append(msg)

    def add_random_news(self):
        """경제 뉴스와 정책 뉴스의 영향 완화 및 점진적 반영"""
        # 뉴스 유형 선택
        msg_type = random.choice([0, 1, 2, 3, 4, 5, 6, 7])

        # 회사 관련 뉴스 (Positive/Negative)
        if msg_type in (0, 1, 4, 6):
            possible_companies = [c for c in self.companies if not c.is_bankrupt]
            if not possible_companies:
                return

            target = random.choice(possible_companies)

            if msg_type in (0, 4):  # 호재 (Positive)
                cands = Message.POSITIVE_MESSAGES_BY_SECTOR.get(target.sector, [])
                if not cands:
                    return
                txt = random.choice(cands).replace("{company}", target.name)

                msg_obj = {
                    "type": "positive",
                    "sector": target.sector,
                    "company": target.name,
                    "text": txt
                }
                self.all_messages.append(msg_obj)
                self.recent_messages.append(msg_obj)
                if len(self.recent_messages) > 37:
                    self.recent_messages.pop(0)

                # 점진적 상승 효과 설정
                impact_pct = random.uniform(0.005, 0.01)  # 0.05% ~ 0.1%로 축소
                duration = random.randint(20, 30)
                target.news_impact = impact_pct / duration
                target.news_impact_days = duration

            else:  # 악재 (Negative)
                cands = Message.NEGATIVE_MESSAGES_BY_SECTOR.get(target.sector, [])
                if not cands:
                    return
                txt = random.choice(cands).replace("{company}", target.name)

                msg_obj = {
                    "type": "negative",
                    "sector": target.sector,
                    "company": target.name,
                    "text": txt
                }
                self.all_messages.append(msg_obj)
                self.recent_messages.append(msg_obj)
                if len(self.recent_messages) > 37:
                    self.recent_messages.pop(0)

                # 점진적 하락 효과 설정
                impact_pct = random.uniform(-0.075, -0.025)  # -0.25% ~ -0.75%로 축소
                duration = random.randint(3, 7)
                target.news_impact = impact_pct / duration
                target.news_impact_days = duration

        elif msg_type in (2, 3):  # 정책 (Policy)
            sector_list = list(Message.POLICY_MESSAGES_BY_SECTOR.keys())
            s = random.choice(sector_list)
            cands = Message.POLICY_MESSAGES_BY_SECTOR.get(s, [])
            if not cands:
                return
            tx = random.choice(cands).replace("{sector}", s)

            msgp = {
                "type": "policy",
                "sector": s,
                "company": None,
                "text": tx
            }
            self.all_messages.append(msgp)
            self.recent_messages.append(msgp)
            if len(self.recent_messages) > 37:
                self.recent_messages.pop(0)

            # 섹터 내 회사 리스트 생성
            sector_companies = [c for c in self.companies if c.sector == s]

            # 섹터 내 일부 회사만 영향 받도록 설정
            sample_size = min(len(sector_companies), max(1, len(self.companies) // 3))  # 크기 조정
            selected_companies = random.sample(sector_companies, k=sample_size)

            # 점진적 영향 적용
            impact_pct = random.uniform(-0.0025, 0.0025)  # ±0.25%로 축소
            duration = random.randint(20, 30)
            for c in selected_companies:
                c.news_impact = impact_pct / duration
                c.news_impact_days = duration

        else:  # 경제 (Economic)
            # 정책 감정 점수 기반 확률 계산
            p_positive = (self.policy_sentiment_score + 30) / 60
            p_positive = max(0.1, min(p_positive, 0.9))

            if random.random() < p_positive:
                impact_pct = random.uniform(0.001, 0.002)  # 상승 0.5%~1.5%
                if not Message.ECONOMIC_NEWS_POSITIVE:
                    return
                newstxt, delta = random.choice(Message.ECONOMIC_NEWS_POSITIVE)
            else:
                impact_pct = random.uniform(-0.002, -0.001)  # 하락 -0.5%~-1.5%
                if not Message.ECONOMIC_NEWS_NEGATIVE:
                    return
                newstxt, delta = random.choice(Message.ECONOMIC_NEWS_NEGATIVE)

            msg_e = {
                "type": "economic",
                "sector": None,
                "company": None,
                "text": newstxt
            }
            self.all_messages.append(msg_e)
            self.recent_messages.append(msg_e)
            if len(self.recent_messages) > 37:
                self.recent_messages.pop(0)

            # 전체 적용 대신 랜덤 20%의 회사만 영향 적용
            sample_size = max(1, len(self.companies) // 5)  # 20% 회사만 선택
            selected_companies = random.sample(self.companies, k=sample_size)
            duration = random.randint(20, 30)
            for c in selected_companies:
                c.news_impact = impact_pct / duration
                c.news_impact_days = duration

            # 정책 감정 점수 업데이트
            self.policy_sentiment_score += delta

    def player_triggered_event(self):
        """플레이어가 트리거한 이벤트"""
        # 플레이어가 특정 이벤트를 트리거할 수 있도록 구현
        # 예시로 특정 회사의 주가를 일시적으로 상승시킴
        if not self.companies:
            return
        target = random.choice(self.companies)
        impact_pct = random.uniform(0.05, 0.15)  # 5% ~ 15% 상승
        self.apply_price_change(target, impact_pct * 100)

        msg = {
            "type": "player_event",
            "sector": target.sector,
            "company": target.name,
            "text": f"[플레이어 이벤트] {target.name}에 대한 긍정적인 플레이어 이벤트로 주가가 {impact_pct*100:.2f}% 상승했습니다."
        }
        self.all_messages.append(msg)
        self.recent_messages.append(msg)

    def handle_company_interactions(self):
        """회사 간 상호작용 관리"""
        # 회사 수 유지 기준
        MIN_COMPANY_COUNT = 17
        TARGET_COMPANY_COUNT = 20

        # 회사 수 유지
        if len(self.companies) < MIN_COMPANY_COUNT:
            self.add_random_companies(TARGET_COMPANY_COUNT - len(self.companies))

        # 상호작용 처리
        for c1 in self.companies:
            if c1.is_bankrupt:
                continue

            # 상호작용 발생 확률 설정
            action_prob = random.random()
            if action_prob < 0.005:  # 0.5% 확률로 계약 체결
                c2 = random.choice(self.companies)
                if c1.id != c2.id and not c2.is_bankrupt:
                    self.contract_deal(c1, c2)

            elif action_prob < 0.01:  # 추가 0.5% 확률로 투자
                c2 = random.choice(self.companies)
                if c1.id != c2.id and not c2.is_bankrupt:
                    self.invest_in_company(c1, c2)

            elif action_prob < 0.015:  # 추가 0.5% 확률로 지분 인수
                c2 = random.choice(self.companies)
                if c1.id != c2.id and not c2.is_bankrupt:
                    self.acquire_shares(c1, c2)

                # 상호작용 발생 확률 설정
                action_prob_inner = random.random()
                if action_prob_inner < 0.01:  # 1% 확률로 특허 획득
                    self.patent_acquisition(c1)
                elif action_prob_inner < 0.02:  # 1% 확률로 신제품 출시
                    self.new_product_release(c1)
                elif action_prob_inner < 0.03:  # 1% 확률로 규제 강화
                    self.regulatory_changes(c1)
                elif action_prob_inner < 0.04:  # 1% 확률로 노사 갈등
                    self.labor_disputes(c1)
                elif action_prob_inner < 0.05:  # 1% 확률로 공급망 문제 발생
                    self.supply_chain_disruptions(c1)

    def contract_deal(self, c1, c2):
        """계약 체결"""
        contract_amount = random.randint(100000, 1000000)

        # 자본 및 부채 조정
        c1.capital += contract_amount * 0.8  # 80% 수익
        c2.capital -= contract_amount  # 계약 비용 지출
        c2.debt += contract_amount * 0.2  # 20% 부채 증가

        # 자본이 음수가 되지 않도록 제한
        if c2.capital < 0:
            c2.capital = 0

        # 부채가 음수가 되지 않도록 제한
        if c2.debt < 0:
            c2.debt = 0

        # 뉴스 메시지 추가
        msg = {
            "type": "contract",
            "sector": c1.sector,
            "company": f"{c1.name} - {c2.name}",
            "text": f"[계약 체결] {c1.name}와 {c2.name}가 {contract_amount:,}원 규모의 계약을 체결"
        }
        self.all_messages.append(msg)
        self.recent_messages.append(msg)

    def patent_acquisition(self, company):
        """특허 획득 이벤트"""
        company.capital *= 1.05  # 변동 축소
        msg = {
            "type": "patent",
            "sector": company.sector,
            "company": company.name,
            "text": f"[특허 획득] {company.name}가 새로운 특허를 획득했습니다."
        }
        self.all_messages.append(msg)
        self.recent_messages.append(msg)

    def new_product_release(self, company):
        """신제품 출시 이벤트"""
        company.capital *= 1.075  # 변동 축소
        msg = {
            "type": "product",
            "sector": company.sector,
            "company": company.name,
            "text": f"[신제품 출시] {company.name}가 신제품을 발표했습니다."
        }
        self.all_messages.append(msg)
        self.recent_messages.append(msg)

    def regulatory_changes(self, company):
        """규제 강화 이벤트"""
        company.capital *= 0.925  # 변동 축소
        msg = {
            "type": "regulation",
            "sector": company.sector,
            "company": company.name,
            "text": f"[규제 강화] {company.name}가 강화된 규제를 받습니다."
        }
        self.all_messages.append(msg)
        self.recent_messages.append(msg)

    def labor_disputes(self, company):
        """노사 갈등 이벤트"""
        company.debt *= 1.1  # 변동 축소
        msg = {
            "type": "labor",
            "sector": company.sector,
            "company": company.name,
            "text": f"[노사 갈등] {company.name}가 노사 갈등을 겪고 있습니다."
        }
        self.all_messages.append(msg)
        self.recent_messages.append(msg)

    def supply_chain_disruptions(self, company):
        """공급망 문제 이벤트"""
        company.capital *= 0.95  # 변동 축소
        msg = {
            "type": "supply",
            "sector": company.sector,
            "company": company.name,
            "text": f"[공급망 문제] {company.name}가 공급망 문제를 겪고 있습니다."
        }
        self.all_messages.append(msg)
        self.recent_messages.append(msg)

    def add_company(self, company):
        self.companies.append(company)

    def apply_price_change(self, company, pct):
        if not company.candles:
            return
        cndl = company.candles[-1]
        for k in ["open", "high", "low", "close"]:
            cndl[k] *= (1 + pct / 100.0)
        if cndl["high"] < cndl["low"]:
            cndl["high"], cndl["low"] = cndl["low"], cndl["high"]
        company.check_bankruptcy(econ_factor=self.economic_factor, current_day=self.day_count)

    def next_day(self, investors, dt):
        self.day_count += 1

        # 정세 업데이트
        self.update_sentiment()

        # 경제적 요인 업데이트
        self.update_economic_factors()

        econ_factor = self.economic_factor

        # 새로운 캔들 추가
        for c in self.companies:
            if not c.is_bankrupt:
                c.update_price_daily(econ_factor=econ_factor, economic_factors=self.economic_factors,
                                     national_factors=self.national_factors)
                c.check_bankruptcy(econ_factor=econ_factor, current_day=self.day_count)

        # 회사 간 상호작용 추가
        self.handle_company_interactions()

        # 봇들의 투자 행동 추가
        for investor in investors:
            if isinstance(investor, Bot):
                investor.make_decisions(self)

        # 파산 처리
        bk = [c for c in self.companies if c.is_bankrupt]
        for bcp in bk:
            msg = {
                "type": "bankrupt",
                "sector": bcp.sector,
                "company": bcp.name,
                "text": f"[파산] {bcp.name} - 장기적 악화로 인한 파산"
            }
            self.all_messages.append(msg)
            self.recent_messages.append(msg)
            self.bankrupt_companies.append(bcp)

            # 파산 팝업을 위한 전역 변수에 추가
            # 파산한 회사가 플레이어가 보유한 주식인지 확인
            player = investors[0]  # 플레이어가 첫 번째 투자자라고 가정
            if player.holdings.get(bcp.id, {}).get('quantity', 0) > 0:
                bankrupt_notifications.append({"text": msg["text"], "timer": 30})  # 3초 동안 표시 (60 FPS 기준)

        self.companies = [c for c in self.companies if not c.is_bankrupt]

        # 신규 회사 추가
        if len(self.companies) < 10:
            self.add_random_companies(12 - len(self.companies))
        elif random.random() < self.company_creation_prob_map.get(self.economic_condition, 0.1):
            self.add_random_companies(1)

        # 뉴스 생성
        if random.random() < 0.7:
            self.generate_random_news()

    def generate_random_news(self):
        """뉴스 생성 로직 수정: 다양한 뉴스 및 이벤트 추가"""
        # 현재는 기존 뉴스 생성 로직을 유지하고, 특별 이벤트를 별도로 처리
        self.add_random_news()

class Investor:
    def __init__(self, name, cash):
        self.name = name
        self.cash = cash
        self.holdings = {}  # {company.id: {"quantity":Q, "avg_price":P} }

    def buy(self, company, quantity):
        if quantity <= 0:
            return False
        if company.is_bankrupt:
            return False  # 파산한 회사는 매수 불가
        cost = company.current_price * quantity
        if cost > self.cash:
            return False
        self.cash -= cost
        if company.id not in self.holdings:
            self.holdings[company.id] = {"quantity": 0, "avg_price": 0.0}
        old_qty = self.holdings[company.id]["quantity"]
        old_avg = self.holdings[company.id]["avg_price"]
        new_qty = old_qty + quantity
        if new_qty > 0:
            new_avg = (old_qty * old_avg + quantity * company.current_price) / new_qty
        else:
            new_avg = 0
        self.holdings[company.id]["quantity"] = new_qty
        self.holdings[company.id]["avg_price"] = new_avg
        logging.info(f"{self.name}이 {company.name}을 {quantity}주 매수했습니다.")
        return True

    def sell(self, company, quantity):
        if quantity <= 0:
            return False
        if company.is_bankrupt:
            return False  # 파산한 회사는 매도 불가
        if company.id not in self.holdings:
            return False
        old_qty = self.holdings[company.id]["quantity"]
        if old_qty < quantity:
            return False
        self.holdings[company.id]["quantity"] = old_qty - quantity
        revenue = company.current_price * quantity
        self.cash += revenue
        if self.holdings[company.id]["quantity"] == 0:
            del self.holdings[company.id]
        logging.info(f"{self.name}이 {company.name}을 {quantity}주 매도했습니다.")
        return True

    def remove_holding(self, company):
        """보유 주식 제거 (제거 버튼 클릭 시 호출)"""
        if company.id in self.holdings:
            del self.holdings[company.id]
            return True
        return False

    def get_portfolio_value(self, market):
        val = self.cash
        for c in market.companies + market.bankrupt_companies:
            if c.id in self.holdings:
                q = self.holdings[c.id]["quantity"]
                p = c.current_price if not c.is_bankrupt else 0  # 파산한 회사는 현재가를 0으로 설정
                val += p * q
        return val

class Bot(Investor):
    def __init__(self, name, cash, strategy="random"):
        super().__init__(name, cash)
        self.strategy = strategy  # 전략 유형: 'random', 'growth', 'sector', 'value', 'momentum'
        self.focus_sector = random.choice(["IT", "의약", "화학", "게임", "에너지", "금융"]) if strategy == "sector" else None

    def make_decisions(self, market):
        """봇의 주식 매매 결정 로직"""
        if self.strategy == "random":
            self.random_strategy(market)
        elif self.strategy == "growth":
            self.growth_strategy(market)
        elif self.strategy == "sector":
            self.sector_strategy(market)
        elif self.strategy == "value":
            self.value_strategy(market)
        elif self.strategy == "momentum":
            self.momentum_strategy(market)

    def random_strategy(self, market):
        """무작위 매매 전략"""
        action = random.choice(["buy", "sell", "hold"])
        if action == "buy":
            company = random.choice(market.companies)
            quantity = random.randint(1, 10)
            self.buy(company, quantity)
            # 뉴스 메시지 추가 가능
        elif action == "sell" and self.holdings:
            company_id = random.choice(list(self.holdings.keys()))
            company = next((c for c in market.companies if c.id == company_id), None)
            if company:
                max_qty = self.holdings[company.id]["quantity"]
                if max_qty >= 1:
                    quantity = random.randint(1, min(5, max_qty))  # 매도 수량 조정
                    self.sell(company, quantity)
                    # 뉴스 메시지 추가 가능

    def growth_strategy(self, market):
        """성장 전략: 저평가된 주식 매수, 고평가된 주식 매도"""
        # 매수: 현재 주가가 최근 평균보다 낮은 회사 선택
        buy_candidates = []
        for company in market.companies:
            if company.is_bankrupt:
                continue
            if len(company.candles) < 5:
                continue
            recent_closes = [c["close"] for c in company.candles[-5:]]
            avg_close = sum(recent_closes) / len(recent_closes)
            if company.current_price < avg_close * 0.95:
                buy_candidates.append(company)
        if buy_candidates:
            company = random.choice(buy_candidates)
            quantity = random.randint(5, 20)
            self.buy(company, quantity)
            # 뉴스 메시지 추가 가능

        # 매도: 현재 주가가 최근 평균보다 높은 회사 선택
        sell_candidates = []
        for company in market.companies:
            if company.is_bankrupt:
                continue
            if company.id not in self.holdings:
                continue
            if len(company.candles) < 5:
                continue
            recent_closes = [c["close"] for c in company.candles[-5:]]
            avg_close = sum(recent_closes) / len(recent_closes)
            if company.current_price > avg_close * 1.05:
                sell_candidates.append(company)
        if sell_candidates:
            company = random.choice(sell_candidates)
            max_qty = self.holdings[company.id]["quantity"]
            if max_qty >= 1:
                quantity = random.randint(1, min(5, max_qty))  # 매도 수량 조정
                self.sell(company, quantity)
                # 뉴스 메시지 추가 가능

    def sector_strategy(self, market):
        """섹터 집중 전략: 특정 섹터에 집중 투자"""
        if not self.focus_sector:
            self.focus_sector = random.choice(["IT", "의약", "화학", "게임", "에너지", "금융"])
        sector_companies = [c for c in market.companies if c.sector == self.focus_sector and not c.is_bankrupt]
        if not sector_companies:
            return
        action = random.choice(["buy", "sell", "hold"])
        if action == "buy":
            company = random.choice(sector_companies)
            quantity = random.randint(10, 30)
            self.buy(company, quantity)
            # 뉴스 메시지 추가 가능

        elif action == "sell" and self.holdings:
            sector_holdings = [c for c in market.companies if c.id in self.holdings and c.sector == self.focus_sector]
            if sector_holdings:
                company = random.choice(sector_holdings)
                max_qty = self.holdings[company.id]["quantity"]
                if max_qty >= 1:
                    quantity = random.randint(1, min(5, max_qty))  # 매도 수량 조정
                    self.sell(company, quantity)
                    # 뉴스 메시지 추가 가능

    def value_strategy(self, market):
        """가치 투자 전략: 저평가된 회사 매수, 고평가된 회사 매도"""
        # 매수: P/E 비율이 낮은 회사 선택 (가치 투자 지표)
        buy_candidates = []
        for company in market.companies:
            if company.is_bankrupt or company.revenue == 0:
                continue
            pe_ratio = company.current_price / (company.net_income if company.net_income > 0 else 1)
            if pe_ratio < 15:  # 예시 임계값
                buy_candidates.append(company)
        if buy_candidates:
            company = random.choice(buy_candidates)
            quantity = random.randint(5, 20)
            self.buy(company, quantity)
            # 뉴스 메시지 추가 가능

        # 매도: P/E 비율이 높은 회사 선택
        sell_candidates = []
        for company in market.companies:
            if company.is_bankrupt or company.id not in self.holdings:
                continue
            pe_ratio = company.current_price / (company.net_income if company.net_income > 0 else 1)
            if pe_ratio > 25:  # 예시 임계값
                sell_candidates.append(company)
        if sell_candidates:
            company = random.choice(sell_candidates)
            max_qty = self.holdings[company.id]["quantity"]
            if max_qty >= 1:
                quantity = random.randint(1, min(5, max_qty))  # 매도 수량 조정
                self.sell(company, quantity)
                # 뉴스 메시지 추가 가능

    def momentum_strategy(self, market):
        """모멘텀 투자 전략: 상승 추세의 주식 매수, 하락 추세의 주식 매도"""
        # 매수: 최근 3일 연속 상승한 회사
        buy_candidates = []
        for company in market.companies:
            if company.is_bankrupt or len(company.candles) < 4:
                continue
            recent_changes = [company.candles[-i]["close"] - company.candles[-i-1]["close"] for i in range(1, 4)]
            if all(change > 0 for change in recent_changes):
                buy_candidates.append(company)
        if buy_candidates:
            company = random.choice(buy_candidates)
            quantity = random.randint(5, 20)
            self.buy(company, quantity)
            # 뉴스 메시지 추가 가능

        # 매도: 최근 3일 연속 하락한 회사
        sell_candidates = []
        for company in market.companies:
            if company.is_bankrupt or company.id not in self.holdings or len(company.candles) < 4:
                continue
            recent_changes = [company.candles[-i]["close"] - company.candles[-i-1]["close"] for i in range(1, 4)]
            if all(change < 0 for change in recent_changes):
                sell_candidates.append(company)
        if sell_candidates:
            company = random.choice(sell_candidates)
            max_qty = self.holdings[company.id]["quantity"]
            if max_qty >= 1:
                quantity = random.randint(1, min(5, max_qty))  # 매도 수량 조정
                self.sell(company, quantity)
                # 뉴스 메시지 추가 가능

# ############################
# 3) 유틸/차트
# ############################

def random_company_name():
    letters = "".join(random.choice(string.ascii_uppercase) for _ in range(3))
    nums = "".join(random.choice(string.digits) for _ in range(2))
    return f"{letters}{nums}"

def create_initial_market():
    mk = Market()
    sector_list = ["IT", "의약", "화학", "게임", "에너지", "금융"]
    for _ in range(23):
        nm = random_company_name()
        st = random.choice(sector_list)
        ip = random.uniform(1000, 50000)
        c = Company(nm, st, ip)
        # 경쟁사 추가 (예시로 2개)
        c.competitors = random.sample([comp.name for comp in mk.companies], k=min(2, len(mk.companies)))
        mk.add_company(c)
    return mk

def draw_text(surface, text, x, y, color=(0, 0, 0), font=None):
    if font is None:
        font = pygame.font.SysFont("malgungothic", 16)
    img = font.render(text, True, color)
    surface.blit(img, (x, y))

# 고정된 캔들 폭 정의
FIXED_CANDLE_WIDTH = 14  # 픽셀 단위

def draw_candlestick_chart(surface, x, y, w, h, candles, font, timeframe_info):
    """
    고정된 캔들 폭으로 캔들스틱 차트를 그립니다.

    매개변수:
        surface (pygame.Surface): 그릴 표면.
        x (int): 차트의 시작 x 좌표.
        y (int): 차트의 시작 y 좌표.
        w (int): 차트의 너비.
        h (int): 차트의 높이.
        candles (list): 캔들스틱 데이터 목록.
        font (pygame.font.Font): 텍스트 폰트.
        timeframe_info (dict): 현재 타임프레임 정보 (group_size).
    """

    # 차트 배경
    pygame.draw.rect(surface, (30, 30, 30), (x, y, w, h))

    if not candles:
        return

    # 고정된 캔들 폭
    cndl_w = FIXED_CANDLE_WIDTH

    # 차트에 표시 가능한 캔들 수 계산
    num_candles_to_display = (w - 40) // cndl_w  # 패딩 고려

    # 마지막 num_candles_to_display 캔들 선택
    candles = candles[-num_candles_to_display:]

    # 표시된 캔들 기준 최대 및 최소 가격 계산
    all_high = [c["high"] for c in candles]
    all_low = [c["low"] for c in candles]
    mxp = max(all_high)
    mnp = min(all_low)

    if mxp == mnp:
        mxp += 1  # 0으로 나누는 것을 방지

    # 가격을 Y 좌표로 변환하는 함수
    def toY(p):
        ratio = (p - mnp) / (mxp - mnp) * 1.7
        return y + h - 20 - ratio * (h - 40)

    # Y축 그리드 선 및 레이블 그리기
    num_labels = 10
    for i in range(num_labels + 1):
        label_price = mnp + (mxp - mnp) * i / num_labels
        label_y = toY(label_price)

        # 그리드 선 그리기
        pygame.draw.line(surface, (80, 80, 80), (x + 20, label_y), (x + w - 120, label_y), 1)

        # 가격 레이블 그리기
        label_text = f"{label_price:.2f}"
        label_surf = font.render(label_text, True, (255, 255, 255))
        label_x = x + w - 100
        surface.blit(label_surf, (label_x, label_y - label_surf.get_height() // 2))

    # 이동 평균선 계산
    def calculate_moving_average(candles, window):
        if len(candles) < window:
            return []
        ma = []
        for i in range(len(candles)):
            if i < window - 1:
                ma.append(None)
            else:
                window_candles = candles[i - window + 1:i + 1]
                avg = sum(c["close"] for c in window_candles) / window
                ma.append(avg)
        return ma

    ma5 = calculate_moving_average(candles, 5)
    ma20 = calculate_moving_average(candles, 10)
    ma60 = calculate_moving_average(candles, 20)
    ma120 = calculate_moving_average(candles, 30)

    # 이동 평균선 그리기
    def draw_moving_average(ma, color):
        points = []
        for i, avg in enumerate(ma):
            if avg is not None:
                points.append((x + 20 + i * cndl_w + cndl_w / 2, toY(avg)))
            else:
                points.append(None)
        # 선 그리기
        prev_point = None
        for point in points:
            if point is not None and prev_point is not None:
                pygame.draw.line(surface, color, prev_point, point, 2)
            if point is not None:
                prev_point = point
            else:
                prev_point = None

    draw_moving_average(ma5, (255, 255, 0))    # 노란색
    draw_moving_average(ma20, (0, 255, 0))     # 초록색
    draw_moving_average(ma60, (0, 0, 255))     # 파란색
    draw_moving_average(ma120, (255, 0, 0))    # 빨간색

    # 이동 평균선 레이블 그리기
    draw_text(surface, "MA5", x + w - 250, y + h, (255, 255, 0), font)
    draw_text(surface, "MA10", x + w - 200, y + h, (0, 255, 0), font)
    draw_text(surface, "MA20", x + w - 140, y + h, (0, 0, 255), font)
    draw_text(surface, "MA30", x + w - 80, y + h, (255, 0, 0), font)

    # 현재 표시되는 캔들 중 저점과 고점 표시
    current_low = min(all_low)
    current_high = max(all_high)
    draw_text(surface, f"최저가: {current_low:.2f}", x + 20, y + h + 30, (255, 255, 255), font)
    draw_text(surface, f"최고가: {current_high:.2f}", x + 20, y + h, (255, 255, 255), font)

    # 캔들 그리기
    for i, cndl in enumerate(candles):
        o = cndl["open"]
        hi = cndl["high"]
        lo = cndl["low"]
        cl = cndl["close"]

        # 캔들의 x 위치 계산
        cx = x + 20 + i * cndl_w

        # 가격을 Y 좌표로 변환
        oy = toY(o)
        cy = toY(cl)
        hy = toY(hi)
        ly = toY(lo)

        # 캔들 색상 결정
        color = (255, 80, 80) if cl >= o else (0, 160, 255)

        # 고저 선 그리기
        line_x = cx + cndl_w / 2
        pygame.draw.line(surface, color, (line_x, hy), (line_x, ly), 1)

        # 시가-종가 사각형 그리기
        rect_x = cx
        rect_width = cndl_w
        rect_height = abs(cy - oy)
        rect_top = min(oy, cy)
        pygame.draw.rect(surface, color, (rect_x, rect_top, rect_width, rect_height))

# ############################
# 4) 전역 상수/변수
# ############################

SCENE_HOME = 0
SCENE_SIMULATION = 1
SCENE_COMPANY_DETAIL = 2
SCENE_TRADE = 3
SCENE_PORTFOLIO = 4
SCENE_GOAL_SUCCESS = 5
SCENE_GOAL_FAILURE = 6

# 목표 설정
GOAL_AMOUNT = 100_000_000  # 1억 원
GOAL_DAYS = 90  # 3개월

# 전역 변수로 investors 선언
investors = []

SCROLLBAR_WIDTH = 12
HEADER_HEIGHT = 40
GAP = 30
SCROLL_SPEED = 30  # 스크롤 속도 (픽셀 단위)

# 파산 알림을 위한 전역 변수 추가
# 각 메시지에 'timer'를 추가하여 표시 시간을 관리
bankrupt_notifications = []

def get_price_diff_string(company):
    """전일대비 등락률 문자열 (e.g. +3.45%)"""
    if len(company.candles) < 2:
        return "(+0.00%)"
    diff_pct = company.get_last_diff_pct()
    sign = "+" if diff_pct > 0 else ""
    return f"({sign}{diff_pct:.2f}%)"

# 타임프레임 설정 수정
TIMEFRAME_OPTIONS = ["하루", "일주일", "한달", "1년"]
timeframe_index = 1

market = None  # 전역 변수로 market 초기화

def switch_timeframe_forward():
    global timeframe_index, market
    timeframe_index = (timeframe_index + 1) % len(TIMEFRAME_OPTIONS)
    market.current_timeframe = get_current_timeframe()

def switch_timeframe_backward():
    global timeframe_index, market
    timeframe_index = (timeframe_index - 1) % len(TIMEFRAME_OPTIONS)
    market.current_timeframe = get_current_timeframe()

def get_current_timeframe():
    return TIMEFRAME_OPTIONS[timeframe_index]

# ############################
# 5) 메인 함수
# ############################

def main():
    global timeframe_index, investors, market, restart_btn_goal, exit_btn_goal, restart_btn_fail, exit_btn_fail

    # 초기화 및 변수 설정
    current_scene_after_trade = SCENE_COMPANY_DETAIL  # 기본값은 회사 상세 화면
    company_list_scroll = 0
    sort_key = "name"
    sort_asc = True
    search_query = ""  # 검색 쿼리 추가

    pygame.init()
    WIDTH, HEIGHT = 1600, 900  # 해상도 확대
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("모의 주식 시뮬레이션 (포트폴리오: 실시간 주가/등락률 + 클릭 시 상세)")

    try:
        base_font = pygame.font.SysFont("malgungothic", 18)
        title_font = pygame.font.SysFont("malgungothic", 23)
        button_font = pygame.font.SysFont("malgungothic", 20)
    except:
        base_font = pygame.font.SysFont("Arial", 18)
        title_font = pygame.font.SysFont("Arial", 23)
        button_font = pygame.font.SysFont("Arial", 20)

    clock = pygame.time.Clock()

    BG_COLOR = (30, 30, 30)
    PANEL_COLOR = (50, 50, 50)
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 80, 80)
    GREEN = (0, 200, 0)
    BLUE = (0, 160, 255)
    DARK_BLUE = (0, 90, 180)
    GRAY = (100, 100, 100)
    LIGHT_GRAY = (170, 170, 170)

    current_scene = SCENE_HOME

    market = create_initial_market()

    # 플레이어 투자자 추가
    investors = [Investor("플레이어", 25000000)]  # 여러 투자자가 필요할 경우 리스트로 관리

    # 봇 투자자 추가
    investors.append(Bot("봇_랜덤1", 5000000, strategy="random"))
    investors.append(Bot("봇_성장1", 7000000, strategy="growth"))
    investors.append(Bot("봇_섹터1", 6000000, strategy="sector"))
    investors.append(Bot("봇_가치1", 8000000, strategy="value"))
    investors.append(Bot("봇_모멘텀1", 7500000, strategy="momentum"))

    investor = investors[0]  # 현재 플레이어를 첫 번째 투자자로 설정
    selected_company = None

    trade_mode = "BUY"
    trade_quantity_str = ""
    error_message = ""

    # DAY_INTERVAL은 이제 고정된 0.5초로 설정
    DAY_INTERVAL = 0.5  # 0.5초마다 주가 업데이트
    day_timer = 0

    LEFT_PANEL_WIDTH = 500
    RIGHT_PANEL_WIDTH = 600

    # panel_x, panel_width, header_y, header_height 정의
    panel_x, panel_y = 20, 100
    panel_width, panel_height = LEFT_PANEL_WIDTH - 40, HEIGHT - 150
    header_y = panel_y + 10
    header_height = 30

    def draw_text_local(surf, txt, x, y, color=WHITE, font=base_font):
        """로컬 텍스트 그리기 함수"""
        t = font.render(txt, True, color)
        surf.blit(t, (x, y))

    class Button:
        """버튼 클래스 정의"""
        def __init__(self, x, y, w, h, text, callback, color=GRAY, hover_color=LIGHT_GRAY, font=button_font, disabled=False):
            self.rect = pygame.Rect(x, y, w, h)
            self.text = text
            self.callback = callback
            self.color = color
            self.hover_color = hover_color
            self.font = font
            self.hovered = False
            self.disabled = disabled  # 버튼 비활성화 상태

        def draw(self, surf):
            """버튼 그리기"""
            if self.disabled:
                current_color = (80, 80, 80)  # 비활성화된 버튼 색상
            else:
                current_color = self.hover_color if self.hovered else self.color
            pygame.draw.rect(surf, current_color, self.rect, border_radius=5)
            txt_surf = self.font.render(self.text, True, (255, 255, 255))
            tx = self.rect.centerx - txt_surf.get_width() // 2
            ty = self.rect.centery - txt_surf.get_height() // 2
            surf.blit(txt_surf, (tx, ty))

        def handle_event(self, event):
            """이벤트 처리"""
            if self.disabled:
                return  # 비활성화된 버튼은 이벤트 무시
            if event.type == pygame.MOUSEMOTION:
                self.hovered = self.rect.collidepoint(event.pos)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.rect.collidepoint(event.pos):
                    self.callback()

    # 홈화면 버튼 콜백 함수
    def on_start_clicked():
        nonlocal current_scene
        current_scene = SCENE_SIMULATION

    def on_exit_clicked():
        pygame.quit()
        sys.exit()

    # 홈화면 버튼 생성
    start_btn = Button(WIDTH // 2 - 100, 400, 200, 60, "시뮬레이션 시작", on_start_clicked, color=DARK_BLUE, hover_color=BLUE)
    exit_btn = Button(WIDTH // 2 - 100, 480, 200, 60, "종료하기", on_exit_clicked, color=RED, hover_color=LIGHT_GRAY)

    # 목표 성공 버튼 (전역으로 생성)
    def on_restart_clicked_goal():
        nonlocal current_scene, investor, day_timer
        global market, bankrupt_notifications
        # 초기화
        market = create_initial_market()
        investors.clear()
        investors.append(Investor("플레이어", 25000000))
        investors.append(Bot("봇_랜덤1", 5000000, strategy="random"))
        investors.append(Bot("봇_성장1", 7000000, strategy="growth"))
        investors.append(Bot("봇_섹터1", 6000000, strategy="sector"))
        investors.append(Bot("봇_가치1", 8000000, strategy="value"))
        investors.append(Bot("봇_모멘텀1", 7500000, strategy="momentum"))
        investor = investors[0]
        current_scene = SCENE_HOME
        day_timer = 0
        bankrupt_notifications.clear()

    def on_exit_clicked_goal():
        pygame.quit()
        sys.exit()

    restart_btn_goal = Button(WIDTH // 2 - 150, HEIGHT // 2, 120, 50, "재시작", on_restart_clicked_goal, color=BLUE, hover_color=LIGHT_GRAY)
    exit_btn_goal = Button(WIDTH // 2 + 30, HEIGHT // 2, 120, 50, "종료하기", on_exit_clicked_goal, color=RED, hover_color=LIGHT_GRAY)

    # 목표 실패 버튼 (전역으로 생성)
    def on_restart_clicked_fail():
        nonlocal current_scene, investor, day_timer
        global market, bankrupt_notifications
        # 초기화
        market = create_initial_market()
        investors.clear()
        investors.append(Investor("플레이어", 10000000))
        investors.append(Bot("봇_랜덤1", 5000000, strategy="random"))
        investors.append(Bot("봇_성장1", 7000000, strategy="growth"))
        investors.append(Bot("봇_섹터1", 6000000, strategy="sector"))
        investors.append(Bot("봇_가치1", 8000000, strategy="value"))
        investors.append(Bot("봇_모멘텀1", 7500000, strategy="momentum"))
        investor = investors[0]
        current_scene = SCENE_HOME
        day_timer = 0
        bankrupt_notifications.clear()

    def on_exit_clicked_fail():
        pygame.quit()
        sys.exit()

    restart_btn_fail = Button(WIDTH // 2 - 150, HEIGHT // 2, 120, 50, "재시작", on_restart_clicked_fail, color=BLUE, hover_color=LIGHT_GRAY)
    exit_btn_fail = Button(WIDTH // 2 + 30, HEIGHT // 2, 120, 50, "종료하기", on_exit_clicked_fail, color=RED, hover_color=LIGHT_GRAY)

    # 홈화면 버튼 그리기 함수
    def show_home_screen():
        """홈 화면 그리기 함수"""
        screen.fill(BG_COLOR)
        title_text = "모의 주식 시뮬레이션"
        title_surf = title_font.render(title_text, True, WHITE)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, 200))
        screen.blit(title_surf, title_rect)
        start_btn.draw(screen)
        exit_btn.draw(screen)

    # 포트폴리오 버튼 콜백 함수
    def on_portfolio_clicked():
        nonlocal current_scene
        current_scene = SCENE_PORTFOLIO

    # 포트폴리오 버튼 생성
    portfolio_btn = Button(20, 20, 150, 50, "포트폴리오", on_portfolio_clicked, color=BLUE, hover_color=DARK_BLUE)

    # 타임프레임 버튼 콜백 함수
    def on_tf_prev():
        switch_timeframe_backward()

    tf_prev_btn = Button(200, 20, 50, 50, "<<", on_tf_prev, color=GRAY, hover_color=LIGHT_GRAY)

    def on_tf_next():
        switch_timeframe_forward()

    tf_next_btn = Button(260, 20, 50, 50, ">>", on_tf_next, color=GRAY, hover_color=LIGHT_GRAY)

    # 검색창 텍스트
    search_text = ""

    # 정렬 함수 정의 (main 함수 내에서 접근 가능하도록)
    def sorting_func(c):
        if sort_key == "price":
            return c.current_price
        elif sort_key == "sector":
            return c.sector
        else:
            return c.name

    # Sell 버튼 리스트 초기화
    portfolio_sell_buttons = []  # 이제 main 함수 내에서 정의

    # 거래를 시작하는 함수 (중복 제거)
    def initiate_trade(mode, return_scene):
        """거래를 시작할 때 호출되는 함수"""
        nonlocal trade_mode, trade_quantity_str, error_message, current_scene, selected_company, current_scene_after_trade
        if selected_company.is_bankrupt and mode == "SELL":
            # 파산한 회사는 매도할 수 없지만 제거는 가능
            error_message = "파산한 회사는 매도할 수 없습니다."
            return
        trade_mode = mode
        trade_quantity_str = ""
        error_message = ""
        selected_company = selected_company  # 이미 설정된 회사
        current_scene_after_trade = return_scene
        current_scene = SCENE_TRADE

    def initiate_remove(company):
        """포트폴리오에서 회사 제거"""
        nonlocal investor
        success = investor.remove_holding(company)
        if success:
            # 제거 성공 시 메시지 추가
            msg_text = f"{investor.name}이 {company.name}을(를) 포트폴리오에서 제거했습니다."
            market.all_messages.append({"type": "trade", "text": msg_text})
            market.recent_messages.append({"type": "trade", "text": msg_text})
        else:
            # 제거 실패 시 메시지 추가
            msg_text = f"{company.name}을(를) 포트폴리오에서 제거하지 못했습니다."
            market.all_messages.append({"type": "trade", "text": msg_text})
            market.recent_messages.append({"type": "trade", "text": msg_text})

    def remove_holding(company):
        """포트폴리오에서 회사 제거"""
        nonlocal investor
        success = investor.remove_holding(company)
        if success:
            # 제거 성공 시 메시지 추가
            msg_text = f"{investor.name}이 {company.name}을(를) 포트폴리오에서 제거했습니다."
            market.all_messages.append({"type": "trade", "text": msg_text})
            market.recent_messages.append({"type": "trade", "text": msg_text})
        else:
            # 제거 실패 시 메시지 추가
            msg_text = f"{company.name}을(를) 포트폴리오에서 제거하지 못했습니다."
            market.all_messages.append({"type": "trade", "text": msg_text})
            market.recent_messages.append({"type": "trade", "text": msg_text})

    def aggregate_candles(candles, group_size):
        """
        주어진 캔들 데이터를 group_size만큼 집계하여 새로운 캔들 데이터를 반환합니다.

        매개변수:
            candles (list): 원본 캔들 데이터 리스트.
            group_size (int): 집계할 그룹 크기.

        반환값:
            aggregated (list): 집계된 캔들 데이터 리스트.
        """
        aggregated = []
        for i in range(0, len(candles), group_size):
            group = candles[i:i + group_size]
            if len(group) == 0:
                continue
            open_price = group[0]["open"]
            close_price = group[-1]["close"]
            high_price = max(c["high"] for c in group)
            low_price = min(c["low"] for c in group)
            aggregated.append({
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price
            })
        return aggregated

    def show_simulation_screen(dt):
        """시뮬레이션 화면 그리기 함수"""
        nonlocal company_list_scroll, sort_key, sort_asc, search_query
        screen.fill(BG_COLOR)

        # 상단 정보 그리기
        top_info_y = 20
        draw_text_local(screen, f"Day {int(market.day_count/48)}", 350, top_info_y, WHITE, base_font)
        if market.policy_sentiment_score < -5:
            color = RED
        elif market.policy_sentiment_score >= 15:
            color = GREEN
        else:
            color = WHITE
        draw_text_local(screen, f"정세: {market.economic_condition} (점수: {market.policy_sentiment_score:.2f})", 450,
                       top_info_y, color, base_font)
        portfolio_btn.draw(screen)
        tf_prev_btn.draw(screen)
        tf_next_btn.draw(screen)
        current_tf = get_current_timeframe()
        draw_text_local(screen, f"TF: {current_tf}", 350, 45, WHITE, base_font)

        # 검색창 그리기
        search_box_rect = pygame.Rect(500, 52, 200, 20)
        pygame.draw.rect(screen, WHITE, search_box_rect, border_radius=5)
        draw_text_local(screen, search_query, 505, 50, BLACK, base_font)
        draw_text_local(screen, "검색:", 450, 50, WHITE, base_font)

        # 왼쪽 패널 그리기
        panel_width, panel_height = LEFT_PANEL_WIDTH - 40, HEIGHT - 150
        pygame.draw.rect(screen, PANEL_COLOR, (panel_x, panel_y, panel_width, panel_height), border_radius=10)

        # 클리핑 영역 설정
        list_clip_rect = pygame.Rect(panel_x + 10, panel_y + 10, panel_width - 20, panel_height - 20)
        screen.set_clip(list_clip_rect)

        # 헤더 그리기
        header_y_local = panel_y + 10
        pygame.draw.rect(screen, DARK_BLUE, (panel_x + 10, header_y_local, panel_width - 20, header_height), border_radius=5)
        draw_text_local(screen, "회사이름", panel_x + 20, header_y_local + 3, WHITE, base_font)
        draw_text_local(screen, "주가", panel_x + 140, header_y_local + 3, WHITE, base_font)
        draw_text_local(screen, "전일비", panel_x + 240, header_y_local + 3, WHITE, base_font)
        draw_text_local(screen, "분야", panel_x + 340, header_y_local + 3, WHITE, base_font)

        # 정렬된 회사 목록 가져오기
        sorted_comps = sorted(market.companies, key=sorting_func, reverse=(not sort_asc))

        # 검색 필터 적용
        if search_query:
            sorted_comps = [c for c in sorted_comps if search_query.lower() in c.name.lower() or search_query.lower() in c.sector.lower()]

        # 최대 표시할 아이템 수 설정
        visible_height = panel_height - 40  # 헤더와 패딩을 제외한 높이
        max_scroll = max(len(sorted_comps) * GAP - visible_height, 0)

        # 스크롤 위치 제한
        company_list_scroll = max(0, min(company_list_scroll, max_scroll))

        # 스크롤바 그리기
        if len(sorted_comps) * GAP > visible_height:
            sbx = panel_x + panel_width - SCROLLBAR_WIDTH - 10
            sby = panel_y + 10
            sbh = panel_height - 20
            pygame.draw.rect(screen, (100, 100, 100), (sbx, sby, SCROLLBAR_WIDTH, sbh))

            # 핸들 높이 계산
            handle_height = max(int(sbh * (visible_height / (len(sorted_comps) * GAP))), 20)
            scroll_ratio = company_list_scroll / max_scroll if max_scroll > 0 else 0
            handle_y = sby + int(scroll_ratio * (sbh - handle_height))
            pygame.draw.rect(screen, (200, 200, 200), (sbx, handle_y, SCROLLBAR_WIDTH, handle_height))

        # 회사 목록 그리기
        start_y = header_y_local + header_height + 10 - company_list_scroll
        for i, comp in enumerate(sorted_comps):
            cy = start_y + i * GAP
            if cy < header_y_local + header_height + 10 or cy > panel_y + panel_height - GAP:
                continue  # 화면에 보이지 않는 항목은 그리지 않음
            price_str = f"{comp.current_price:.2f}"
            diff_str = get_price_diff_string(comp)
            if len(comp.candles) > 1:
                old_cl = comp.candles[-2]["close"]
                new_cl = comp.candles[-1]["close"]
                cc = GREEN if new_cl > old_cl else RED if new_cl < old_cl else WHITE
            else:
                cc = WHITE

            # 회사 이름 표시 (파산한 경우 빨간색과 "파산" 라벨 추가)
            if comp.is_bankrupt:
                draw_text_local(screen, f"{comp.name} (파산)", panel_x + 20, cy, RED, base_font)
            else:
                draw_text_local(screen, comp.name, panel_x + 20, cy, cc, base_font)

            # 주가
            draw_text_local(screen, price_str, panel_x + 140, cy, cc, base_font)
            # 전일비
            draw_text_local(screen, diff_str, panel_x + 240, cy, cc, base_font)
            # 분야
            draw_text_local(screen, comp.sector, panel_x + 340, cy, cc, base_font)

        # 클리핑 해제
        screen.set_clip(None)

        # 중앙 패널 그리기 (기존 코드 유지 및 경제 지표 추가)
        center_x = LEFT_PANEL_WIDTH
        center_w = WIDTH - LEFT_PANEL_WIDTH - RIGHT_PANEL_WIDTH - 60
        center_y = 100
        center_h = HEIGHT - 150
        pygame.draw.rect(screen, PANEL_COLOR, (center_x, center_y, center_w, center_h), border_radius=10)

        # 투자자 정보 및 경제 지표 추가
        cx = center_x + 20
        cy = center_y + 20
        draw_text_local(screen, f"투자자: {investor.name}", cx, cy, WHITE, base_font)
        cy += 30
        draw_text_local(screen, f"보유 현금: {investor.cash:.2f}원", cx, cy, WHITE, base_font)
        cy += 30
        p_val = investor.get_portfolio_value(market)
        draw_text_local(screen, f"총자산 (현금 + 주식): {p_val:.2f}원", cx, cy, WHITE, base_font)
        cy += 40

        # 목표 정보 추가
        draw_text_local(screen, "[목표]", cx, cy, WHITE, title_font)
        cy += 30
        draw_text_local(screen, f"3개월(90일) 안에 1억 원 달성하기", cx, cy, WHITE, base_font)
        cy += 30
        current_progress_pct = min(investor.cash / GOAL_AMOUNT * 100, 100)
        progress_bar_width = 200
        progress_bar_height = 25
        pygame.draw.rect(screen, GRAY, (cx, cy, progress_bar_width, progress_bar_height))
        pygame.draw.rect(screen, GREEN, (cx, cy, progress_bar_width * (current_progress_pct / 100), progress_bar_height))
        draw_text_local(screen, f"{current_progress_pct:.2f}% 달성", cx + 5, cy + 2, BLACK, base_font)
        cy += 40

        # 중앙 패널에 경제 지표 추가
        econ_factors = market.economic_factors
        draw_text_local(screen, "[경제 지표]", cx, cy, WHITE, title_font)
        cy += 30
        draw_text_local(screen, f"GDP 성장률: {econ_factors['gdp_growth']:.2f}%", cx, cy, WHITE, base_font)
        cy += 25
        draw_text_local(screen, f"인플레이션율: {econ_factors['inflation']:.2f}%", cx, cy, WHITE, base_font)
        cy += 25
        draw_text_local(screen, f"금리: {econ_factors['interest_rate']:.2f}%", cx, cy, WHITE, base_font)
        cy += 25
        draw_text_local(screen, f"실업률: {econ_factors['unemployment']:.2f}%", cx, cy, WHITE, base_font)
        cy += 25
        draw_text_local(screen, f"환율: {econ_factors['exchange_rate']:.2f}원/USD", cx, cy, WHITE, base_font)
        cy += 25
        draw_text_local(screen, f"원자재 비용: {econ_factors['raw_material_cost']:.2f}", cx, cy, WHITE, base_font)
        cy += 25
        draw_text_local(screen, f"정치적 안정성: {econ_factors['political_stability']:.2f}", cx, cy, WHITE, base_font)
        cy += 25
        draw_text_local(screen, f"기술 혁신 지수: {econ_factors['innovation_index']:.2f}", cx, cy, WHITE, base_font)
        cy += 40

        # 중앙 패널에 국가 지표 추가
        national_factors = market.national_factors
        draw_text_local(screen, "[국가 지표]", cx, cy, WHITE, title_font)
        cy += 30
        draw_text_local(screen, f"국가 총 자산: {national_factors['total_assets']:.2f}조", cx, cy, WHITE, base_font)
        cy += 25
        draw_text_local(screen, f"출산율: {national_factors['birth_rate']:.2f}명", cx, cy, WHITE, base_font)
        cy += 25
        draw_text_local(screen, f"인구: {national_factors['population']:,}명", cx, cy, WHITE, base_font)
        cy += 40

        # 검색 결과 수 표시
        draw_text_local(screen, f"검색 결과: {len(sorted_comps)}개", cx, cy, WHITE, base_font)
        cy += 20

        # 검색 관련 안내
        draw_text_local(screen, "[왼쪽 회사 클릭 -> 상세 / ESC -> 홈]", cx, cy, GRAY, base_font)
        draw_text_local(screen, "가운데 포트폴리오 클릭 -> 상세", cx, cy + 25, GRAY, base_font)

        # 오른쪽 패널 그리기 (뉴스) 그리기
        right_x = WIDTH - RIGHT_PANEL_WIDTH - 40
        pygame.draw.rect(screen, PANEL_COLOR, (right_x, 100, RIGHT_PANEL_WIDTH, HEIGHT - 150), border_radius=10)
        draw_text_local(screen, "최신 뉴스", right_x + 20, 120, WHITE, title_font)
        ny = 160
        for msg in market.recent_messages[-27:]:
            if ny > HEIGHT:
                break
            draw_text_local(screen, "- " + msg["text"], right_x + 20, ny, WHITE, base_font)
            ny += 25

        # 파산 팝업 표시
        for notif in bankrupt_notifications[:]:
            popup_text = notif["text"]
            popup_timer = notif["timer"]
            if popup_timer > 0:
                popup_font = pygame.font.SysFont("malgungothic", 30)
                popup_surf = popup_font.render(popup_text, True, RED)
                popup_rect = popup_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                screen.blit(popup_surf, popup_rect)
                notif["timer"] -= 1  # 타이머 감소
            else:
                bankrupt_notifications.remove(notif)

    tf_prev_btn_detail = Button(1300, 20, 50, 50, "<<", on_tf_prev, color=GRAY, hover_color=LIGHT_GRAY)

    tf_next_btn_detail = Button(1360, 20, 50, 50, ">>", on_tf_next, color=GRAY, hover_color=LIGHT_GRAY)

    def show_company_detail_screen(company):
        """회사 상세 정보 화면 그리기 함수"""
        screen.fill(BG_COLOR)
        draw_text_local(screen, f"[{company.name}] 상세 정보", 50, 50, WHITE, title_font)

        top_info_y = 20
        draw_text_local(screen, f"Day {int(market.day_count / 48)}", 1450, top_info_y, WHITE, base_font)

        if market.policy_sentiment_score < -5:
            color = RED
        elif market.policy_sentiment_score >= 15:
            color = GREEN
        else:
            color = WHITE
        draw_text_local(screen, f"정세: {market.economic_condition} (점수: {market.policy_sentiment_score:.2f})", 1010,
                       top_info_y + 37, color, base_font)

        tf_prev_btn_detail.draw(screen)
        tf_next_btn_detail.draw(screen)
        current_tf = get_current_timeframe()
        draw_text_local(screen, f"TF: {current_tf}", 1450, 45, WHITE, base_font)

        # 차트 그리기
        group_size = market.timeframes[market.current_timeframe]["group_size"]
        aggregated_candles = aggregate_candles(company.candles, group_size)
        candles_to_display = (800 - 40) // FIXED_CANDLE_WIDTH - 7  # 차트 너비가 800이라고 가정
        display_candles = aggregated_candles[-candles_to_display:]

        chart_x, chart_y = 50, 400
        chart_w, chart_h = 800, 400
        timeframe_info = {
            "group_size": group_size
        }

        draw_candlestick_chart(screen, chart_x, chart_y, chart_w, chart_h, display_candles, base_font, timeframe_info)

        py = 30
        if len(company.candles) > 1:
            oldp = company.candles[-2]["close"]
            newp = company.candles[-1]["close"]
            df = newp - oldp
            df_pct = (df / oldp * 100) if oldp != 0 else 0
            diff_str = f"{df:+.2f}원 ({df_pct:+.2f}%)"
        else:
            diff_str = "(첫날)"
        lines = [
            f"분야: {company.sector}",
            f"현재 주가: {company.current_price:.2f}원" + (" (파산)" if company.is_bankrupt else ""),
            f"전일 대비: {diff_str}",
            f"자본: {company.capital:.2f}, 부채: {company.debt:.2f}",

        ]
        for line in lines:
            draw_text_local(screen, line, 300, py, WHITE, base_font)
            py += 30

        py = 30

        lines = [
            f"매출: {company.revenue:.2f}원",
            f"순이익: {company.net_income:.2f}원",
            f"시장 점유율: {company.market_share:.2f}%",
            f"경쟁사: {', '.join(company.competitors) if company.competitors else '없음'}"
        ]
        for line in lines:
            draw_text_local(screen, line, 650, py, WHITE, base_font)
            py += 30

        py = 30

        # 회사의 성장 가능성과 위험 요소 시각화
        growth = "높음" if company.market_share > 5 else "보통" if company.market_share > 2 else "낮음"
        risk = "높음" if company.debt / max(company.capital, 1) > 1 else "보통" if company.debt / max(company.capital, 1) > 0.5 else "낮음"
        draw_text_local(screen, f"파산 가능성: {risk}", 50, py, RED if risk == "높음" else WHITE, base_font)
        py += 40

        # 회사 상세 화면에 매수/매도 버튼 추가
        buy_btn_disabled = Button(50, 100, 100, 40, "매수하기", on_buy_clicked, color=GREEN, hover_color=LIGHT_GRAY, disabled=company.is_bankrupt)
        sell_btn_disabled = Button(170, 100, 100, 40, "매도하기", on_sell_clicked, color=RED, hover_color=LIGHT_GRAY, disabled=company.is_bankrupt)

        buy_btn_disabled.draw(screen)
        sell_btn_disabled.draw(screen)

        # 관련 뉴스
        right_x = 900
        draw_text_local(screen, "[관련 뉴스]", right_x - 20, 50, WHITE, title_font)
        ny = 90
        detail_filtered = []

        # 관련 뉴스 필터링 수정: economic 타입은 무조건 포함
        for msg_obj in market.all_messages:
            if msg_obj["type"] in ["positive", "negative", "random", "contract", "investment", "acquisition", "merge", "partner"]:
                # 회사 이름이 포함된 뉴스 필터링
                if company.name in msg_obj.get("company", ""):
                    detail_filtered.append(msg_obj["text"])
            elif msg_obj["type"] in ["policy", "economic", "trade"]:
                # 정책, 경제, 거래 뉴스는 조건없이 포함
                detail_filtered.append(msg_obj["text"])

        # 필터링된 뉴스 출력
        for tx in detail_filtered[-29:]:
            if ny > HEIGHT - 100:
                break
            draw_text_local(screen, "- " + tx, right_x - 15, ny, WHITE, base_font)
            ny += 25

        back_btn.draw(screen)

    def on_buy_clicked():
        nonlocal current_scene, trade_mode, trade_quantity_str, error_message, current_scene_after_trade
        if selected_company.is_bankrupt:
            error_message = "파산한 회사는 매수할 수 없습니다."
            return
        trade_mode = "BUY"
        trade_quantity_str = ""
        error_message = ""
        current_scene_after_trade = SCENE_COMPANY_DETAIL
        current_scene = SCENE_TRADE

    def on_sell_clicked():
        nonlocal current_scene, trade_mode, trade_quantity_str, error_message, current_scene_after_trade
        if selected_company.is_bankrupt:
            error_message = "파산한 회사는 매도할 수 없습니다."
            return
        trade_mode = "SELL"
        trade_quantity_str = ""
        error_message = ""
        current_scene_after_trade = SCENE_COMPANY_DETAIL
        current_scene = SCENE_TRADE

    # 매수/매도 버튼 생성 (이미 전역으로 생성)
    buy_btn = Button(50, 100, 100, 40, "매수하기", on_buy_clicked, color=GREEN, hover_color=LIGHT_GRAY)
    sell_btn = Button(170, 100, 100, 40, "매도하기", on_sell_clicked, color=RED, hover_color=LIGHT_GRAY)

    def on_back():
        nonlocal current_scene
        current_scene = SCENE_SIMULATION

    # 뒤로가기 버튼 생성
    back_btn = Button(WIDTH - 150, HEIGHT - 80, 120, 50, "뒤로가기", on_back, color=DARK_BLUE, hover_color=BLUE)

    def on_trade_confirm():
        nonlocal current_scene, trade_quantity_str, selected_company, error_message, current_scene_after_trade
        try:
            qty = int(trade_quantity_str)
        except ValueError:
            error_message = "정수만 입력!"
            return
        if not selected_company:
            error_message = "회사 선택 오류!"
            return
        if selected_company.is_bankrupt:
            error_message = "파산한 회사는 거래할 수 없습니다!"
            return

        if trade_mode == "BUY":
            max_buy_qty = int(investor.cash // selected_company.current_price) if selected_company.current_price > 0 else 0
            if qty > max_buy_qty:
                error_message = f"최대 매수 가능 수량은 {max_buy_qty}입니다."
                return
            ok = investor.buy(selected_company, qty)
            if not ok:
                error_message = "매수 실패!(잔고 부족/수량 <= 0)"
                return
        elif trade_mode == "SELL":
            max_sell_qty = investor.holdings.get(selected_company.id, {}).get("quantity", 0)
            if qty > max_sell_qty:
                error_message = f"최대 매도 가능 수량은 {max_sell_qty}입니다."
                return
            ok = investor.sell(selected_company, qty)
            if not ok:
                error_message = "매도 실패!(수량 부족/수량 <= 0)"
                return

        # 거래 성공 시 알림 메시지 추가
        if trade_mode == "BUY":
            msg_text = f"{investor.name}이 {selected_company.name}을 {qty}주 매수했습니다."
            market.all_messages.append({"type": "trade", "text": msg_text})
            market.recent_messages.append({"type": "trade", "text": msg_text})
        elif trade_mode == "SELL":
            msg_text = f"{investor.name}이 {selected_company.name}을 {qty}주 매도했습니다."
            market.all_messages.append({"type": "trade", "text": msg_text})
            market.recent_messages.append({"type": "trade", "text": msg_text})

        error_message = ""
        current_scene = current_scene_after_trade  # 거래 완료 후 원래 화면으로 돌아감

    def on_trade_cancel():
        nonlocal current_scene
        current_scene = current_scene_after_trade  # 거래 취소 시 원래 화면으로 돌아감

    # 확인/취소 버튼 생성
    confirm_btn = Button(WIDTH // 2 - 130, 700, 120, 50, "확인", on_trade_confirm, color=GREEN, hover_color=LIGHT_GRAY)
    cancel_btn = Button(WIDTH // 2 + 10, 700, 120, 50, "취소", on_trade_cancel, color=RED, hover_color=LIGHT_GRAY)

    def show_trade_screen():
        """트레이드 화면 그리기 함수"""
        screen.fill(BG_COLOR)
        info_tx = f"[{selected_company.name}] - {trade_mode}"
        draw_text_local(screen, info_tx, WIDTH // 2 - 80, 100, WHITE, title_font)
        draw_text_local(screen, "수량 입력 후 확인 또는 취소", WIDTH // 2 - 115, 160, GRAY, base_font)

        # 입력 박스 그리기
        in_rect = pygame.Rect(WIDTH // 2 - 100, 200, 200, 40)
        pygame.draw.rect(screen, WHITE, in_rect, border_radius=5)
        draw_text_local(screen, trade_quantity_str, in_rect.x + 10, in_rect.y + 10, BLACK, base_font)

        # 매수/매도 최대 수량 계산 및 표시
        if trade_mode == "BUY":
            max_buy_qty = int(
                investor.cash // selected_company.current_price) if selected_company.current_price > 0 else 0
            max_buy_qty = max_buy_qty if max_buy_qty > 0 else 0
            draw_text_local(screen, f"최대 매수 가능 수량: {max_buy_qty}", WIDTH // 2 - 100, 260, WHITE, base_font)
        elif trade_mode == "SELL":
            max_sell_qty = investor.holdings.get(selected_company.id, {}).get("quantity", 0)
            draw_text_local(screen, f"최대 매도 가능 수량: {max_sell_qty}", WIDTH // 2 - 100, 260, WHITE, base_font)

        confirm_btn.draw(screen)
        cancel_btn.draw(screen)

        if error_message:
            draw_text_local(screen, error_message, WIDTH // 2 - 100, 300, RED, base_font)

    # 포트폴리오 화면 버튼 콜백 함수
    def on_portfolio_back():
        nonlocal current_scene
        current_scene = SCENE_SIMULATION

    # 포트폴리오 뒤로가기 버튼 생성
    portfolio_back_btn = Button(50, HEIGHT - 80, 120, 50, "뒤로가기", on_portfolio_back, color=DARK_BLUE, hover_color=BLUE)

    def get_related_news(company):
        """특정 회사와 관련된 뉴스 필터링"""
        related_news = []

        # 뉴스 메시지 필터링
        for msg in market.all_messages:
            if msg["type"] in ["positive", "negative", "random", "contract", "investment", "acquisition", "merge", "partner"]:
                # 회사 이름이 포함된 뉴스 필터링
                if company.name in msg.get("company", ""):
                    related_news.append(msg["text"])
            elif msg["type"] in ["policy", "economic", "trade"]:
                # 정책, 경제, 거래 뉴스는 조건없이 포함
                related_news.append(msg["text"])

        return related_news[-30:]  # 최근 30개의 관련 뉴스 반환

    def show_portfolio_screen():
        """포트폴리오 화면 그리기 함수"""
        nonlocal portfolio_sell_buttons, company_list_scroll, sort_key, sort_asc
        portfolio_sell_buttons.clear()
        screen.fill(BG_COLOR)
        draw_text_local(screen, "[포트폴리오]", 50, 50, WHITE, title_font)

        py = 100
        draw_text_local(screen, f"보유 현금: {investor.cash:.2f}원", 50, py, WHITE, base_font)
        py += 30
        val = investor.get_portfolio_value(market)
        draw_text_local(screen, f"총 자산: {val:.2f}원", 50, py, WHITE, base_font)
        py += 50

        # 테이블 헤더 그리기
        header_y = py
        pygame.draw.rect(screen, DARK_BLUE, (40, header_y + 2, 850, 30), border_radius=5)
        draw_text_local(screen, "회사이름", 50, header_y + 5, WHITE, base_font)
        draw_text_local(screen, "수량", 200, header_y + 5, WHITE, base_font)
        draw_text_local(screen, "평균 매수가", 270, header_y + 5, WHITE, base_font)
        draw_text_local(screen, "현재가", 400, header_y + 5, WHITE, base_font)
        draw_text_local(screen, "전일비", 500, header_y + 5, WHITE, base_font)
        draw_text_local(screen, "등락률", 600, header_y + 5, WHITE, base_font)
        draw_text_local(screen, "평가액", 700, header_y + 5, WHITE, base_font)
        draw_text_local(screen, "매도/제거", 800, header_y + 5, WHITE, base_font)  # 매도/제거 버튼 헤더 추가
        py += 40

        # 라인 목록 초기화
        portfolio_line_rects = []
        portfolio_sell_buttons.clear()

        # 보유 종목 표시 (활성 회사 + 파산 회사)
        held_companies = [c for c in (market.companies + market.bankrupt_companies) if c.id in investor.holdings]
        for c in held_companies:
            data = investor.holdings[c.id]
            qty = data["quantity"]
            avgp = data["avg_price"]
            currp = c.current_price if not c.is_bankrupt else 0  # 파산한 회사는 현재가를 0으로 설정
            # 전일비
            diff_pct = c.get_last_diff_pct()
            sign = "+" if diff_pct > 0 else ""
            diff_str = f"{sign}{diff_pct:.2f}%"
            # 등락률(= (현재가 - 평단)/평단 *100)
            if avgp > 0:
                profit_pct = (currp - avgp) / avgp * 100
            else:
                profit_pct = 0
            sign2 = "+" if profit_pct > 0 else ""
            profit_str = f"{sign2}{profit_pct:.2f}%"

            eval_amount = currp * qty

            # 색상 설정
            profit_color = GREEN if profit_pct > 0 else RED if profit_pct < 0 else WHITE

            # 화면에 표시
            line_y = py
            # 회사 이름 표시 (파산한 경우 빨간색과 "파산" 라벨 추가)
            if c.is_bankrupt:
                draw_text_local(screen, f"{c.name} (파산)", 50, line_y, RED, base_font)
            else:
                draw_text_local(screen, c.name, 50, line_y, WHITE, base_font)

            # 수량
            draw_text_local(screen, str(qty), 200, line_y, WHITE, base_font)
            # 평균 매수가
            draw_text_local(screen, f"{avgp:.2f}", 270, line_y, WHITE, base_font)
            # 현재가
            draw_text_local(screen, f"{currp:.2f}", 400, line_y, WHITE, base_font)
            # 전일비
            draw_text_local(screen, diff_str, 500, line_y, WHITE, base_font)
            # 등락률
            draw_text_local(screen, profit_str, 600, line_y, profit_color, base_font)
            # 평가액
            draw_text_local(screen, f"{eval_amount:.2f}", 700, line_y, WHITE, base_font)

            # 매도 또는 제거 버튼 생성
            if c.is_bankrupt:
                # 파산한 회사는 '제거' 버튼
                remove_button = Button(820, line_y - 3, 60, 30, "제거", lambda c=c: initiate_remove(c), color=RED, hover_color=LIGHT_GRAY, font=button_font)
                portfolio_sell_buttons.append(remove_button)
            else:
                # 일반 회사는 '매도' 버튼
                sell_button = Button(820, line_y - 3, 60, 30, "매도", lambda c=c: initiate_trade("SELL", SCENE_PORTFOLIO), color=RED, hover_color=LIGHT_GRAY, font=button_font, disabled=c.is_bankrupt)
                portfolio_sell_buttons.append(sell_button)

            # 회사별 포트폴리오 라인 클릭 영역
            line_rect = pygame.Rect(50, line_y - 10, 750, 30)
            portfolio_line_rects.append((line_rect, c))

            py += 40

        # 우측 상단에 보유 주식 관련 뉴스 표시
        right_x = 900  # 포트폴리오 테이블이 끝나는 x 위치에 따라 조정
        news_y = 150
        draw_text_local(screen, "보유 주식 관련 뉴스", right_x, news_y - 30, WHITE, title_font)
        news_y += 40

        # 보유 주식 관련 뉴스 필터링
        held_sectors = set(c.sector for c in held_companies)
        held_company_names = set(c.name for c in held_companies)

        related_news = []
        for msg_obj in market.all_messages:
            if msg_obj["type"] == "policy":
                if msg_obj.get("sector") in held_sectors:
                    related_news.append(msg_obj["text"])
            elif msg_obj["type"] == "economic":
                related_news.append(msg_obj["text"])
            elif msg_obj.get("company") in held_company_names:
                related_news.append(msg_obj["text"])
            elif msg_obj["type"] in ["merge", "investment", "contract", "partner", "trade"]:
                if any(comp in msg_obj.get("company", "") for comp in held_company_names):
                    related_news.append(msg_obj["text"])

        # 최신 30개의 관련 뉴스 표시
        for news in related_news[-27:]:
            if news_y > HEIGHT:  # 화면 아래로 넘어가지 않도록 제한
                break
            draw_text_local(screen, "- " + news, right_x + 10, news_y, WHITE, base_font)
            news_y += 25

        portfolio_back_btn.draw(screen)

        # Sell 또는 Remove 버튼 그리기
        for btn in portfolio_sell_buttons:
            btn.draw(screen)
    # ... 중간 코드 생략 ...

    # ############################
    # 6) 목표 화면 함수
    # ############################

    def show_goal_success_screen():
        """목표 달성 성공 화면 그리기 함수"""
        screen.fill(BG_COLOR)
        success_font = pygame.font.SysFont("malgungothic", 40)
        success_text = "축하합니다! 목표를 달성했습니다!"
        success_surf = success_font.render(success_text, True, GREEN)
        success_rect = success_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
        screen.blit(success_surf, success_rect)

        py = 400

        draw_text_local(screen, f"보유 현금: {investor.cash:.2f}원", WIDTH // 2 - 125, py, WHITE, button_font)

        # 버튼 그리기 (전역 변수 사용)
        restart_btn_goal.draw(screen)
        exit_btn_goal.draw(screen)

    def show_goal_failure_screen():
        """목표 달성 실패 화면 그리기 함수"""
        screen.fill(BG_COLOR)
        failure_font = pygame.font.SysFont("malgungothic", 40)
        failure_text = "아쉽습니다! 목표를 달성하지 못했습니다."
        failure_surf = failure_font.render(failure_text, True, RED)
        failure_rect = failure_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        screen.blit(failure_surf, failure_rect)

        # 버튼 그리기 (전역 변수 사용)
        restart_btn_fail.draw(screen)
        exit_btn_fail.draw(screen)

    # ############################
    # 7) 메인 루프 및 실행
    # ############################

    # 메인 루프
    running = True
    while running:
        dt = clock.tick(30) / 400.0  # 초 단위로 변경 (60 FPS 기준)

        if current_scene in [SCENE_SIMULATION, SCENE_PORTFOLIO, SCENE_COMPANY_DETAIL]:
            day_timer += dt
            if day_timer >= DAY_INTERVAL:
                day_timer -= DAY_INTERVAL
                market.next_day(investors, dt)

            # 목표 달성 여부 확인
            portfolio_value = investor.get_portfolio_value(market)
            if investor.cash >= GOAL_AMOUNT:
                current_scene = SCENE_GOAL_SUCCESS
            elif market.day_count/48 >= GOAL_DAYS:
                current_scene = SCENE_GOAL_FAILURE

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # 홈화면
            if current_scene == SCENE_HOME:
                start_btn.handle_event(event)
                exit_btn.handle_event(event)

            elif current_scene == SCENE_SIMULATION:
                portfolio_btn.handle_event(event)
                tf_prev_btn.handle_event(event)
                tf_next_btn.handle_event(event)

                # MOUSEWHEEL 처리
                if event.type == pygame.MOUSEWHEEL:
                    mx, my = pygame.mouse.get_pos()
                    if panel_x <= mx <= panel_x + panel_width:
                        company_list_scroll -= event.y * SCROLL_SPEED
                        # 스크롤 위치 제한
                        sorted_comps = sorted(market.companies, key=sorting_func, reverse=(not sort_asc))
                        if search_query:
                            sorted_comps = [c for c in sorted_comps if search_query.lower() in c.name.lower() or search_query.lower() in c.sector.lower()]
                        visible_height = panel_height - 40  # 헤더와 패딩을 제외한 높이
                        max_scroll = max(len(sorted_comps) * GAP - visible_height, 0)
                        company_list_scroll = max(0, min(company_list_scroll, max_scroll))

                if current_scene == SCENE_SIMULATION:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:  # 왼클릭
                            mx, my = event.pos
                            # 헤더 클릭 -> 정렬
                            if (panel_x + 10 <= mx <= panel_x + 10 + panel_width - 20) and (header_y <= my <= header_y + header_height):
                                if (panel_x + 20 <= mx < panel_x + 140):
                                    if sort_key == "name":
                                        sort_asc = not sort_asc
                                    else:
                                        sort_key = "name"
                                        sort_asc = True
                                elif (panel_x + 140 <= mx < panel_x + 240):
                                    if sort_key == "price":
                                        sort_asc = not sort_asc
                                    else:
                                        sort_key = "price"
                                        sort_asc = True
                                elif (panel_x + 340 <= mx < panel_x + 440):
                                    if sort_key == "sector":
                                        sort_asc = not sort_asc
                                    else:
                                        sort_key = "sector"
                                        sort_asc = True

                            # 검색창 클릭
                            if pygame.Rect(500, 52, 200, 20).collidepoint(mx, my):
                                pygame.key.set_repeat(500, 50)  # 텍스트 입력 반응 속도 조절

                            # 회사 목록 클릭
                            if (panel_x <= mx <= panel_x + panel_width) and (panel_y + header_height + 20 <= my <= panel_y + panel_height):
                                sorted_comps = sorted(market.companies, key=sorting_func, reverse=(not sort_asc))
                                if search_query:
                                    sorted_comps = [c for c in sorted_comps if search_query.lower() in c.name.lower() or search_query.lower() in c.sector.lower()]
                                list_start_y = panel_y + header_height + 10 - company_list_scroll
                                for i, comp in enumerate(sorted_comps):
                                    cy = list_start_y + i * GAP
                                    rr = pygame.Rect(panel_x + 10, cy, panel_width - 20, GAP)
                                    if rr.collidepoint(mx, my):
                                        selected_company = comp
                                        current_scene = SCENE_COMPANY_DETAIL
                                        break

                    if event.type == pygame.KEYDOWN:
                        if current_scene == SCENE_SIMULATION:
                            if event.key == pygame.K_ESCAPE:
                                current_scene = SCENE_HOME
                            elif event.key == pygame.K_BACKSPACE:
                                search_query = search_query[:-1]
                            else:
                                if event.unicode.isprintable():
                                    search_query += event.unicode

            elif current_scene == SCENE_COMPANY_DETAIL:
                tf_prev_btn_detail.handle_event(event)
                tf_next_btn_detail.handle_event(event)

                buy_btn.handle_event(event)
                sell_btn.handle_event(event)
                back_btn.handle_event(event)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        current_scene = SCENE_SIMULATION

            elif current_scene == SCENE_TRADE:
                confirm_btn.handle_event(event)
                cancel_btn.handle_event(event)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        current_scene = current_scene_after_trade
                    elif event.key == pygame.K_RETURN:
                        on_trade_confirm()
                    elif event.key == pygame.K_BACKSPACE:
                        trade_quantity_str = trade_quantity_str[:-1]
                    else:
                        if event.unicode.isdigit() or (event.unicode == "-" and len(trade_quantity_str) == 0):
                            trade_quantity_str += event.unicode

            elif current_scene == SCENE_PORTFOLIO:
                portfolio_back_btn.handle_event(event)
                # Sell 또는 Remove 버튼 이벤트 처리
                for btn in portfolio_sell_buttons:
                    btn.handle_event(event)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        current_scene = SCENE_SIMULATION

            elif current_scene in [SCENE_GOAL_SUCCESS, SCENE_GOAL_FAILURE]:
                if current_scene == SCENE_GOAL_SUCCESS:
                    restart_btn_goal.handle_event(event)
                    exit_btn_goal.handle_event(event)
                elif current_scene == SCENE_GOAL_FAILURE:
                    restart_btn_fail.handle_event(event)
                    exit_btn_fail.handle_event(event)

        # 장면별 그리기
        if current_scene == SCENE_HOME:
            show_home_screen()
        elif current_scene == SCENE_SIMULATION:
            show_simulation_screen(dt)
        elif current_scene == SCENE_COMPANY_DETAIL and selected_company:
            show_company_detail_screen(selected_company)
        elif current_scene == SCENE_TRADE:
            show_trade_screen()
        elif current_scene == SCENE_PORTFOLIO:
            show_portfolio_screen()
        elif current_scene == SCENE_GOAL_SUCCESS:
            show_goal_success_screen()
        elif current_scene == SCENE_GOAL_FAILURE:
            show_goal_failure_screen()

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
