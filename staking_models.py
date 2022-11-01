from django.db import models
from core.models import TimeStampeModel
# Create your models here.
from django.utils import timezone
from nft import models as nft_models
from NuriAdmin import models as Admin_models
import datetime


class StakingObjects(TimeStampeModel):
    year = models.CharField("년도", max_length=4, null=False, blank=False)
    round = models.CharField("회차", max_length=3, null=False, blank=False)

    end_TVL = models.IntegerField("종료 시점 TVL", default=0)
    TVL = models.IntegerField("TVL", default=0)

    cap_reword = models.FloatField("최대 지급량", default=0)
    
    to_do_reword = models.FloatField("해당 회차 누적 지급량", default=0)
    payed_reword = models.FloatField("지급한 지급량", default=0)

    min_amount = models.CharField("최소 참여 수량", max_length=20, null=False, blank=False)
    max_amount = models.CharField("최대 참여 수량", max_length=20, null=False, blank=False)

    start_date = models.DateTimeField("시작 날짜")
    end_date = models.DateTimeField("종료 날짜")

    is_start_staking = models.BooleanField("스테이킹 시작 여부", default=False)
    is_end_staking = models.BooleanField("스테이킹 종료 여부", default=False)
    is_close_staking = models.BooleanField("스테이킹 숨김 여부",default=False)
    
    class Meta:
        verbose_name_plural = "스테이킹 오브젝트"

    def __str__(self):
        return f"{self.year} - {self.round}R"

    @property
    def year_round(self):
        """
        year과 round를 반환.
        """
        return f"{self.year} - {self.round}R"

    def GMT_time(self):
        """
        현재 시간을 GMT시간으로 반환하는 함수 (-9 시간)
        """
        GMT_start_date = self.start_date - datetime.timedelta(hours=9)
        GMT_end_date = self.end_date - datetime.timedelta(hours=9)
        return {
            "GMT_start_date": GMT_start_date,
            "GMT_end_date": GMT_end_date,
        }

    def check_start_date(self):
        """
        시작일이 되었는지 체크하는 함수.
        """
        if timezone.now() - self.start_date >= datetime.timedelta(0):
            return True
        return False

    def add_TVL(self):
        """
        해당 스테이킹 오브젝트를 가진 스테이킹옵션오브젝트들을 필터링 하고 이 들의 TVL값을 더해 해당 객체의 TVL 값에 저장한다.
        """
        option_TVL = StakingOptionObjects.objects.filter(staking_objects=self).aggregate(models.Sum('TVL'))
        self.TVL = option_TVL["TVL__sum"]
        self.save()

    def check_end_date(self):
        """
            django의 내부 함수인 timezone.now()로 현재 설정된 지역 시간대에 맞는 현재시간을 가져온다.
            그 후 설정한 종료 날짜와 빼기 연산을 하여 그값이 0(datetime type)보다 큰지 확인하고 이보다 클경우
            True 반환(종료 날짜를 지낫다는 것) 아닌 경우 False 반환( 아직 종료 날짜가 되지 않았다는 것)
        """
        if timezone.now() - self.end_date >= datetime.timedelta(0):
            return True
        return False

    def call_staking_option(self):
        staking_options = StakingOptionObjects.objects.filter(staking_objects=self)
        return staking_options


class StakingOptionObjects(TimeStampeModel):
    select_option = (
        ("NRFB", "NRFB"),
        ("", ""),
        ("", ""),
        ("", ""),
    )
    apr = models.IntegerField("APR", default=0)

    staking_objects = models.ForeignKey(StakingObjects, related_name="staking_objects", on_delete=models.CASCADE, )

    TVL = models.FloatField("TVL", default=0)

    option = models.CharField("선택 옵션", max_length=15, choices=select_option, default="NRFB")

    class Meta:
        verbose_name_plural = "스테이킹 옵션"


class UserStaking(TimeStampeModel):
    staking_objects = models.ForeignKey(StakingObjects, on_delete=models.SET_NULL, null=True,blank=False)
    staking_option = models.ForeignKey(StakingOptionObjects, on_delete=models.SET_NULL, null=True, blank=False)

    user_address = models.TextField("유저 지갑 주소", default="")
    owner_address = models.TextField("재단 지갑 주소", default="")

    is_user_send = models.BooleanField("유저 송금 여부", default=None,null=True)
    tx_hash = models.TextField("유저가 보낸 트랜잭션", default="")
    amount = models.IntegerField("송금량", default=0)

    burn_nft = models.OneToOneField(nft_models.NFTCard, on_delete=models.SET_NULL, default=None,null=True)

    is_reward = models.BooleanField("리워드 지급여부", default=False , null=True)
    reward_tx_hash = models.TextField("리워드 해시", default="")
    apr = models.FloatField("연 이자율", default=0)
    dir = models.FloatField("일 이자율", default=0)

    acc_int = models.FloatField("누적 된 이자", default=0)
    last_acc_date = models.DateTimeField("마지막 누적 일자", default=timezone.now)
    reward_amount = models.FloatField("지급한 리워드 양", default=None, null=True)
    
    class Meta:
        verbose_name_plural = "유저 스테이킹 예치 정보"

    @property
    def GMT_time(self):
        GMT_start_date = self.created - datetime.timedelta(hours=9)

        return GMT_start_date

    def apr_calculation(self):
        if self.burn_nft is not None:
            token_rate = self.burn_nft.nft_info.rate.boost
        else:
            token_rate = 1

        self.apr = self.staking_option.apr * token_rate

        self.dir = (self.apr / 365)

        self.save()

    def get_reward_stats(self):
        if self.is_reward:
            return True
        else:
            return False

    def usd_deposit(self):
        """
            amount를 usd로 환산하여 반환
        """
        usd = self.amount * float(Admin_models.NRFBInfo.objects.first().price)
        return usd



class StakingTransactionHistory(TimeStampeModel):
    action_list = (
        ("Deposit", "Deposit"),
        ("Withdraw", "Withdraw"),
    )
    action = models.CharField("목적", max_length=20, choices=action_list)

    from_address = models.CharField("보낸 주소", max_length=150, null=False, blank=False)
    to_address = models.CharField("받은 주소", max_length=150, null=False, blank=False)

    tx_hash = models.CharField("해쉬값", max_length=150, null=False, blank=True,default="")
    amount = models.IntegerField("송금량", default=0)

    staking_objects = models.ForeignKey(StakingObjects, on_delete=models.SET_NULL, null=True, blank=False)
    staking_option = models.ForeignKey(StakingOptionObjects, on_delete=models.SET_NULL, null=True, blank=False)

    user_staking = models.ForeignKey(UserStaking, on_delete=models.SET_NULL, null=True, default=None)

    burn_nft = models.ForeignKey(nft_models.NFTCard, on_delete=models.SET_NULL, null=True, default=None)

    error_count = models.IntegerField("에러횟수", default=0)

    is_stats = models.BooleanField("성공 여부", default=None, null=True)
    
    class Meta:
        verbose_name_plural = "[히스토리] Deposit / Withdraw 히스토리"
    
    @property
    def get_burn_history(self):
        if self.burn_nft:
            burn_nft = nft_models.BurnHistory.objects.get(
                from_address = self.from_address,
                token_id = self.burn_nft.token_id
            )
            print(burn_nft)
            return burn_nft
        else:
            return None


    def get_stats(self):
        if self.is_stats:
            return "Success"
        elif self.is_stats is False:
            return "False"
        else:
            return "Processing"

    @property
    def GMT_time(self):
        GMT_start_date = self.created - datetime.timedelta(hours=9)

        return GMT_start_date

    def return_to_alert(self):
        return self.action,self.created.strftime("%B %d, %Y")


class RewardHistory(TimeStampeModel):
    from_address = models.CharField("보낸 주소", max_length=150, null=False, blank=False)
    to_address = models.CharField("받은 주소", max_length=150, null=False, blank=False)

    tx_hash = models.CharField("해쉬값", max_length=150, null=False, blank=False)
    amount = models.IntegerField("리워드 지급 금액", default=0)

    staking_objects = models.ForeignKey(StakingObjects, on_delete=models.SET_NULL, null=True, blank=False)
    staking_option = models.ForeignKey(StakingOptionObjects, on_delete=models.SET_NULL, null=True, blank=False)

    user_staking = models.OneToOneField(UserStaking, on_delete=models.SET_NULL, default=None, null=True,blank=False)

    error_count = models.IntegerField("에러횟수",default=0)

    is_stats = models.BooleanField("성공 여부", default=None, null=True)
    
    class Meta:
        verbose_name_plural = "[히스토리] 리워드 지급 히스토리"

    @property
    def GMT_time(self):
        GMT_start_date = self.created - datetime.timedelta(hours=9)
        return GMT_start_date

    def return_to_alert(self):
        return "Pay Reward" ,self.created.strftime("%B %d, %Y")

    def check_one_day(self):
        if timezone.now() - self.created >= datetime.timedelta(0):
            return True
        return False