from django.shortcuts import render
from . import models as staking_models
# Create your views here.
from nft import models as nft_models
from NuriAdmin import models as Admin_models
from django.http import JsonResponse
from core.views import check_server_inspection



@check_server_inspection
def index(request):
    """
    """
    context = dict()
    staking_obj = staking_models.StakingObjects.objects.filter(
        is_close_staking = False
    )
    if not staking_obj:
        return render(request, "PC_20220527/staking/staking.html")

    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

    if request.method == "GET" and is_ajax:
        user_address = request.GET.get("user_address")

        staking_obj_id = request.GET.get("staking_select_obj")
        if staking_obj_id and staking_obj != "":
            staking_select_obj = staking_obj.get(id=staking_obj_id)
        else:
            staking_select_obj = staking_obj.last()
        staking_options = staking_models.StakingOptionObjects.objects.filter(
            staking_objects__id=staking_select_obj.id
        )
        if user_address and user_address != "":
            user_staking_objs = staking_models.UserStaking.objects.filter(
                user_address = user_address,
                staking_objects__id = staking_select_obj.id
            )
            if user_staking_objs:
                for user_staking_obj in user_staking_objs:
                    print(user_staking_obj.staking_option)
                    staking_options = staking_options.exclude(
                        id = user_staking_obj.staking_option.id
                    )

                context["do_staking"] = user_staking_objs

            context["staking_options"] = staking_options
            context["staking_select_obj"] = staking_select_obj
            context["staking_obj"] = staking_obj
            return render(request, "PC_20220527/staking/earn_part.html",context)
        else:
            context["staking_options"] = staking_options
            context["staking_select_obj"] = staking_select_obj
            context["staking_obj"] = staking_obj
            return render(request, "PC_20220527/staking/earn_part.html", context)
    elif request.method == "GET" and request.GET.get("round"):

        staking_select_obj = staking_obj.get(id=request.GET.get("round"))
        staking_options = staking_models.StakingOptionObjects.objects.filter(
            staking_objects__id=staking_select_obj.id
        )
        context["staking_options"] = staking_options
        context["staking_select_obj"] = staking_select_obj
        context["staking_obj"] = staking_obj
        return render(request, "PC_20220527/staking/staking.html", context)
    else:
        staking_select_obj = staking_obj.last()
        staking_options = staking_models.StakingOptionObjects.objects.filter(
            staking_objects__id=staking_select_obj.id
        )
        context["staking_options"] = staking_options
        context["staking_select_obj"] = staking_select_obj
        context["staking_obj"] = staking_obj
        return render(request, "PC_20220527/staking/staking.html", context)


@check_server_inspection
def staking_detail(request, pk):
    """
    """
    try:
        staking_option = staking_models.StakingOptionObjects.objects.get(
            id = pk
        )
        staking_obj = staking_option.staking_objects

        owner_BEP20 = Admin_models.NuriAdminAddress.objects.get(
            token_kind='BEP20'
        )
        owner_ERC721 = Admin_models.NuriAdminAddress.objects.get(
            token_kind='ERC721'
        )
        is_main = Admin_models.ServerInspection.objects.first().is_main
        context = {
            "staking_option": staking_option,
            "owner_ERC721":owner_ERC721,
            "owner_BEP20":owner_BEP20,
            "staking_obj":staking_obj,
            "is_main":is_main
        }
    except Exception as e:
        print(str(e))
        raise

    if request.method == "GET" and request.GET.get("user_address"):
        user_address = request.GET.get("user_address")
        if user_address and user_address != "":
            user_nft = nft_models.NFTCard.objects.filter(
                nft_owner=user_address,
                is_mint=True,
                is_burn=False,
            )
            context["user_nft"] = user_nft
            try:
                user_staking_obj = staking_models.UserStaking.objects.get(
                    staking_option = staking_option,
                    user_address = user_address
                )
                context["user_staking_obj"] = user_staking_obj

                price = Admin_models.NRFBInfo.objects.first().price

                udt = user_staking_obj.acc_int * price
                print("user_nft",user_nft)

                context["udt"] = udt

                return render(request, "PC_20220527/staking/user_staking_info.html", context)

            except Exception as e:
                print(str(e))
                return render(request, "PC_20220527/staking/user_staking_info.html", context)
        else:
            context["empty_address"] = True


    return render(request,"PC_20220527/staking/staking_detail.html",context)


@check_server_inspection
def user_staking_detail(request,pk):
    """
    """
    user_staking = staking_models.UserStaking.objects.get(
        id=pk,
    )
    context = {
        "user_staking": user_staking,
        "staking_obj": user_staking.staking_objects,
        "staking_option": user_staking.staking_option
    }
    if request.method == 'GET':
        user_address = request.GET.get("user_address")
        if user_address and user_address != "":
            action = request.GET.get("action")
            print(action)
            user_staking = staking_models.UserStaking.objects.get(
                user_address = user_address,
                id = pk,
            )
            user_tr_history = staking_models.StakingTransactionHistory.objects.select_related("user_staking").filter(
                user_staking = user_staking
            )
            try:
                user_reward_history = staking_models.RewardHistory.objects.get(
                    to_address = user_address,
                    user_staking =user_staking
                )
            except Exception as e:
                user_reward_history = None
            print(user_reward_history)
            context["user_tr_historys"] = user_tr_history,
            context["user_staking"] = user_staking,
            context["user_reward_history"] = user_reward_history
            context["action"]= action

            return render(request, "PC_20220527/staking/staking_detail_list_part.html",context)


    return render(request,"PC_20220527/staking/my_staking_detail.html",context)


@check_server_inspection
def request_deposit(request):
    """
    """
    owner = Admin_models.NuriAdminAddress.objects.get(
        token_kind = "BEP20"
    )
    if request.method == "POST":
        from_address = request.POST.get("from_address")
        to_address = request.POST.get("to_address")
        tx_hash = request.POST.get("tx_hash")
        amount = request.POST.get("amount")
        staking_id = request.POST.get("staking_id")
        staking_option_id = request.POST.get("staking_option_id")
        token_id = request.POST.get("token_id")

        if token_id and token_id != "":
            try:
                burn_nft = nft_models.NFTCard.objects.get(
                    nft_owner = from_address,
                    token_id = token_id,
                    is_burn = False,
                    is_mint = True,
                )
                burn_nft.is_burn = None
                burn_nft.save()


            except Exception as e:
                Admin_models.StakingError.objects.create(
                    error_str = "Deposit token_id get error " + str(e),
                    error_function = "staking_deposit",
                    error_from_address = from_address,
                    error_to_address = to_address,
                )

                burn_nft = None
        else:
            burn_nft = None

        if to_address.casefold() != owner.owner_address.casefold():
            raise
        try:
            staking_obj = staking_models.StakingObjects.objects.get(
                id = staking_id
            )
            staking_option = staking_models.StakingOptionObjects.objects.get(
                id = staking_option_id
            )
        except Exception:
            raise

        user_staking_obj, is_created = staking_models.UserStaking.objects.get_or_create(
            staking_objects = staking_obj,
            staking_option = staking_option,
            user_address = from_address,
            owner_address = owner.owner_address,
        )
        user_staking_obj.is_user_send = None
        user_staking_obj.save()
        if burn_nft:
            user_staking_obj.burn_nft = burn_nft
            nft_models.BurnHistory.objects.create(
                from_address=from_address,
                to_address="",
                tx_hash=None,
                token_id=token_id,
                is_stats=None,
            )

        if is_created:
            user_staking_obj.is_user_send = None
            user_staking_obj.apr = staking_option.apr
            user_staking_obj.save()

        staking_models.StakingTransactionHistory.objects.create(
            action = "Deposit",
            from_address = from_address,
            to_address = to_address,
            tx_hash = tx_hash,
            amount = amount,
            staking_objects = staking_obj,
            staking_option = staking_option,
            user_staking= user_staking_obj,
            burn_nft = burn_nft
        )

        return JsonResponse(
            {
                "result":True,
                "user_staking_id": user_staking_obj.id
            }
        )

        pass
    else:
        return JsonResponse(
            {
                "result": False
            }
        )


@check_server_inspection
def request_withdraw(request):
    """
    """
    if request.method == "POST" and request.is_ajax:
        user_address = request.POST.get("user_address")
        staking_obj_id = request.POST.get("staking_obj_id")
        staking_option_id = request.POST.get("staking_option_id")
        amount = request.POST.get("amount")

        try:
            staking_obj = staking_models.StakingObjects.objects.get(
                id=staking_obj_id
            )
            staking_option = staking_models.StakingOptionObjects.objects.get(
                id=staking_option_id
            )
            user_staking = staking_models.UserStaking.objects.get(
                staking_objects=staking_obj,
                staking_option=staking_option,
                user_address=user_address,
            )
            user_staking.is_user_send = None
            user_staking.save()
            if user_staking.amount < int(amount):
                return JsonResponse(
                    {"result": False,
                     "error_str": "You don't have enough deposits"
                     }
                )
            withdraw_history = staking_models.StakingTransactionHistory.objects.create(
                action="Withdraw",
                to_address=user_address,
                amount=amount,
                user_staking=user_staking,
                staking_objects=staking_obj,
                staking_option=staking_option,
                is_stats=None,
            )

            return JsonResponse(
                {
                    "result": True,
                    "user_staking_id": user_staking.id
                }
            )
        except Exception as e:
            print(str(e))
            return JsonResponse(
                {"result": False}
            )
    else:
        return JsonResponse(
            {"result": False}
        )


@check_server_inspection
def request_pay_reward(request):
    """
    """
    if request.method == "POST":

        user_address = request.POST.get("user_address")
        usdr_staking_id = request.POST.get("user_staking_id")
        try:
            user_staking = staking_models.UserStaking.objects.get(
                id = usdr_staking_id,
                user_address = user_address,
            )
            user_staking.is_reward = None
            user_staking.save()
            reward_obj, is_create = staking_models.RewardHistory.objects.get_or_create(
                to_address=user_address,
                user_staking=user_staking,
                staking_objects = user_staking.staking_objects,
                staking_option = user_staking.staking_option,
            )
            if is_create:
                reward_obj.amount = (user_staking.amount + user_staking.acc_int)
                reward_obj.is_stats = None
                reward_obj.save()

                return JsonResponse({"result":"지급완료"})
            else:
                return JsonResponse({"result": False})
        except:
            return JsonResponse({"result":False})

    return JsonResponse({"result":False})
