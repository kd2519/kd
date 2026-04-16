import base64
import hashlib
from datetime import datetime, timedelta
from captcha.views import CaptchaStore, captcha_image
from django.contrib import auth
from django.contrib.auth import login
from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Q
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.conf import settings
from application import dispatch
from dvadmin.system.models import Users
from dvadmin.utils.json_response import ErrorResponse, DetailResponse
from dvadmin.utils.request_util import save_login_log
from dvadmin.utils.serializers import CustomModelSerializer
from dvadmin.utils.validator import CustomValidationError
from django.core.validators import RegexValidator
import random
from django.core.cache import cache
import re
from rest_framework_simplejwt.authentication import JWTAuthentication
class ChangePasswordSerializer(serializers.Serializer):
    oldPassword = serializers.CharField(required=True, max_length=128)
    newPassword = serializers.CharField(required=True, max_length=128)
    newPassword2 = serializers.CharField(required=True, max_length=128)

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user

        old_pwd = attrs.get("oldPassword", "").strip()
        new_pwd = attrs.get("newPassword", "").strip()
        new_pwd2 = attrs.get("newPassword2", "").strip()

        if not old_pwd or not new_pwd or not new_pwd2:
            raise CustomValidationError("参数不能为空")

        if new_pwd != new_pwd2:
            raise CustomValidationError("两次密码不匹配")

        # 1. 校验旧密码
        verify_password = check_password(old_pwd, user.password)

        # 兼容项目里历史 md5 -> make_password 的存储方式
        if not verify_password:
            old_pwd_md5 = hashlib.md5(old_pwd.encode(encoding="UTF-8")).hexdigest()
            verify_password = check_password(old_pwd_md5, user.password)

        # 再兼容一层历史双 md5 场景（参考你现有 user.py 中 change_password 的写法）
        if not verify_password:
            old_pwd_md5_twice = hashlib.md5(old_pwd_md5.encode(encoding="UTF-8")).hexdigest()
            verify_password = check_password(old_pwd_md5_twice, user.password)

        if not verify_password:
            raise CustomValidationError("旧密码不正确")

        # 2. 新密码不能与旧密码相同
        if old_pwd == new_pwd:
            raise CustomValidationError("新密码不能与旧密码相同")

        # 3. 基础强度校验
        self.validate_password_strength(new_pwd, user)

        return attrs

    def validate_password_strength(self, password: str, user):
        """
        企业安全基础版密码强度校验
        可按需继续增强
        """
        if len(password) < 8:
            raise CustomValidationError("新密码长度不能少于8位")

        if len(password) > 64:
            raise CustomValidationError("新密码长度不能超过64位")

        # 至少包含字母和数字
        if not re.search(r"[A-Za-z]", password):
            raise CustomValidationError("新密码必须包含字母")

        if not re.search(r"\d", password):
            raise CustomValidationError("新密码必须包含数字")

        # 可选：至少一个特殊字符
        if not re.search(r"[~!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
            raise CustomValidationError("新密码必须包含特殊字符")

        # 不允许包含用户名
        username = getattr(user, "username", "") or ""
        if username and username.lower() in password.lower():
            raise CustomValidationError("新密码不能包含用户名")

        # 不允许常见弱密码
        weak_passwords = {
            "12345678",
            "123456789",
            "1234567890",
            "password",
            "password123",
            "admin123",
            "admin123456",
            "qwerty123",
            "11111111",
            "00000000",
        }
        if password.lower() in weak_passwords:
            raise CustomValidationError("新密码过于简单，请更换更强的密码")

class ChangePasswordView(APIView):
    """
    登录后修改密码（增强版）
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        print("Authorization =", request.headers.get("Authorization"))
        print("request.user =", request.user)
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        new_pwd = serializer.validated_data.get("newPassword")

        # 参考现有项目逻辑：明文 -> md5 -> make_password
        md5_pwd = hashlib.md5(new_pwd.encode(encoding="UTF-8")).hexdigest()
        user.password = make_password(md5_pwd)

        # 密码修改成功后，清空登录错误计数
        if hasattr(user, "login_error_count"):
            user.login_error_count = 0

        # 修改密码计数 +1（和你当前系统逻辑保持一致）
        if hasattr(user, "pwd_change_count"):
            user.pwd_change_count += 1

        user.save()

        # 记录安全审计/登录日志
        try:
            save_login_log(request=request)
        except Exception:
            pass

        return DetailResponse(data=None, msg="密码修改成功，请重新登录")
class SendResetCodeSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=50)
    mobile = serializers.CharField(max_length=20)

    def validate(self, attrs):
        username = attrs.get("username")
        mobile = attrs.get("mobile")

        user = Users.objects.filter(username=username, mobile=mobile).first()
        if not user:
            raise CustomValidationError("用户名和手机号不匹配")

        attrs["user"] = user
        return attrs


class SendResetCodeView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = SendResetCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        code = str(random.randint(100000, 999999))
        cache_key = f"reset_pwd_code:{user.username}:{user.mobile}"
        cache.set(cache_key, code, timeout=300)

        # 开发阶段：直接打印到控制台
        print(f"[找回密码验证码] username={user.username}, mobile={user.mobile}, code={code}")

        return DetailResponse(msg="验证码已发送（开发环境请查看后端控制台）")

class ResetPasswordByCodeSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=50)
    mobile = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=6)
    password = serializers.CharField()
    rePassword = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get("username")
        mobile = attrs.get("mobile")
        code = attrs.get("code")
        password = attrs.get("password")
        re_password = attrs.get("rePassword")

        if password != re_password:
            raise CustomValidationError("两次密码不一致")

        user = Users.objects.filter(username=username, mobile=mobile).first()
        if not user:
            raise CustomValidationError("用户不存在或手机号不匹配")

        cache_key = f"reset_pwd_code:{username}:{mobile}"
        saved_code = cache.get(cache_key)
        if not saved_code:
            raise CustomValidationError("验证码已过期，请重新发送")

        if str(saved_code) != str(code):
            raise CustomValidationError("验证码错误")

        attrs["user"] = user
        attrs["cache_key"] = cache_key
        return attrs


class ResetPasswordByCodeView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = ResetPasswordByCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        cache_key = serializer.validated_data["cache_key"]
        password = serializer.validated_data["password"]

        # 和当前项目登录逻辑保持一致：明文 -> md5 -> make_password
        md5_password = hashlib.md5(password.encode("utf-8")).hexdigest()
        user.password = make_password(md5_password)
        user.login_error_count = 0
        user.is_active = True
        user.save()

        cache.delete(cache_key)
        return DetailResponse(msg="密码重置成功")

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=50)
    mobile = serializers.CharField()
    password = serializers.CharField()
    rePassword = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get("username")
        mobile = serializers.CharField(
            max_length=11,
            validators=[
                RegexValidator(
                    regex=r'^1[3-9]\d{9}$',
                    message='手机号格式不正确，必须是11位数字，以1开头'
                )
            ]
        )
        password = attrs.get("password")
        re_password = attrs.get("rePassword")

        if password != re_password:
            raise CustomValidationError("两次密码不一致")

        if Users.objects.filter(username=username).exists():
            raise CustomValidationError("用户名已存在")

        if Users.objects.filter(mobile=mobile).exists():
            raise CustomValidationError("电话已存在")

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("rePassword", None)

        # 参考 UserCreateSerializer：先 md5，再 make_password
        md5_password = hashlib.md5(password.encode("utf-8")).hexdigest()
        final_password = make_password(md5_password)

        user = Users.objects.create(
            username=validated_data["username"],
            mobile=validated_data["mobile"],
            name=validated_data["username"],
            password=final_password,
            is_active=True,
        )
        return user


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return DetailResponse(
            data={
                "userId": user.id,
                "username": user.username,
            },
            msg="注册成功"
        )

class CaptchaView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        # 生成验证码 key
        hashkey = CaptchaStore.generate_key()
        store = CaptchaStore.objects.get(hashkey=hashkey)
        # 获取图片响应
        img_response = captcha_image(request, hashkey)
        # 转为 base64
        image_base64 = base64.b64encode(img_response.content).decode('utf-8')
        data = {
            "key": store.id,
            "image_base": "data:image/png;base64," + image_base64,
        }
        return DetailResponse(data=data, msg="success")


class LoginSerializer(TokenObtainPairSerializer):
    """
    登录的序列化器:
    重写djangorestframework-simplejwt的序列化器
    """
    captcha = serializers.CharField(
        max_length=6, required=False, allow_null=True, allow_blank=True
    )

    class Meta:
        model = Users
        fields = "__all__"
        read_only_fields = ["id"]

    default_error_messages = {"no_active_account": _("账号/密码错误")}

    def validate(self, attrs):
        captcha = self.initial_data.get("captcha", None)
        if dispatch.get_system_config_values("base.captcha_state"):
            if captcha is None:
                raise CustomValidationError("验证码不能为空")
            self.image_code = CaptchaStore.objects.filter(
                id=self.initial_data["captchaKey"]
            ).first()
            five_minute_ago = datetime.now() - timedelta(hours=0, minutes=5, seconds=0)
            if self.image_code and five_minute_ago > self.image_code.expiration:
                self.image_code and self.image_code.delete()
                raise CustomValidationError("验证码过期")
            else:
                if self.image_code and (
                    self.image_code.response == captcha
                    or self.image_code.challenge == captcha
                ):
                    self.image_code and self.image_code.delete()
                else:
                    self.image_code and self.image_code.delete()
                    raise CustomValidationError("图片验证码错误")
        try:
            user = Users.objects.get(
                Q(username=attrs['username']) | Q(email=attrs['username']) | Q(mobile=attrs['username']))
        except Users.DoesNotExist:
            raise CustomValidationError("您登录的账号不存在")
        except Users.MultipleObjectsReturned:
            raise CustomValidationError("您登录的账号存在多个,请联系管理员检查登录账号唯一性")
        if not user.is_active:
            raise CustomValidationError("账号已被锁定,联系管理员解锁")
        try:
            # 必须重置用户名为username,否则使用邮箱手机号登录会提示密码错误
            attrs['username'] = user.username
            data = super().validate(attrs)
            data["username"] = self.user.username
            data["name"] = self.user.name
            data["userId"] = self.user.id
            data["avatar"] = self.user.avatar
            data['user_type'] = self.user.user_type
            data['pwd_change_count'] = self.user.pwd_change_count
            dept = getattr(self.user, 'dept', None)
            if dept:
                data['dept_info'] = {
                    'dept_id': dept.id,
                    'dept_name': dept.name,
                }
            role = getattr(self.user, 'role', None)
            if role:
                data['role_info'] = role.values('id', 'name', 'key')
            request = self.context.get("request")
            request.user = self.user
            # 记录登录日志
            save_login_log(request=request)
            user.login_error_count = 0
            user.save()
            return {"code": 2000, "msg": "请求成功", "data": data}
        except Exception as e:
            user.login_error_count += 1
            if user.login_error_count >= 5:
                user.is_active = False
                user.save()
                raise CustomValidationError("账号已被锁定,联系管理员解锁")
            user.save()
            count = 5 - user.login_error_count
            raise CustomValidationError(f"账号/密码错误;重试{count}次后将被锁定~")


class LoginView(TokenObtainPairView):
    """
    登录接口
    """
    serializer_class = LoginSerializer
    permission_classes = []

    # def post(self, request, *args, **kwargs):
    #     # username可能携带的不止是用户名，可能还是用户的其它唯一标识 手机号 邮箱
    #     username = request.data.get('username',None)
    #     if username is None:
    #         return ErrorResponse(msg="参数错误")
    #     password = request.data.get('password',None)
    #     if password is None:
    #         return ErrorResponse(msg="参数错误")
    #     captcha = request.data.get('captcha',None)
    #     if captcha is None:
    #         return ErrorResponse(msg="参数错误")
    #     captchaKey = request.data.get('captchaKey',None)
    #     if captchaKey is None:
    #         return ErrorResponse(msg="参数错误")
    #     if dispatch.get_system_config_values("base.captcha_state"):
    #         if captcha is None:
    #             raise CustomValidationError("验证码不能为空")
    #         self.image_code = CaptchaStore.objects.filter(
    #             id=captchaKey
    #         ).first()
    #         five_minute_ago = datetime.now() - timedelta(hours=0, minutes=5, seconds=0)
    #         if self.image_code and five_minute_ago > self.image_code.expiration:
    #             self.image_code and self.image_code.delete()
    #             raise CustomValidationError("验证码过期")
    #         else:
    #             if self.image_code and (
    #                     self.image_code.response == captcha
    #                     or self.image_code.challenge == captcha
    #             ):
    #                 self.image_code and self.image_code.delete()
    #             else:
    #                 self.image_code and self.image_code.delete()
    #                 raise CustomValidationError("图片验证码错误")
    #     try:
    #         # 手动通过 user 签发 jwt-token
    #         user = Users.objects.get(username=username)
    #     except:
    #         return DetailResponse(msg='该账号未注册')
    #     # 获得用户后，校验密码并签发token
    #     print(make_password(password),user.password)
    #     if check_password(make_password(password),user.password):
    #         return DetailResponse(msg='密码错误')
    #     result = {
    #        "name":user.name,
    #         "userId":user.id,
    #         "avatar":user.avatar,
    #     }
    #     dept = getattr(user, 'dept', None)
    #     if dept:
    #         result['dept_info'] = {
    #             'dept_id': dept.id,
    #             'dept_name': dept.name,
    #             'dept_key': dept.key
    #         }
    #     role = getattr(user, 'role', None)
    #     if role:
    #         result['role_info'] = role.values('id', 'name', 'key')
    #     refresh = LoginSerializer.get_token(user)
    #     result["refresh"] = str(refresh)
    #     result["access"] = str(refresh.access_token)
    #     # 记录登录日志
    #     request.user = user
    #     save_login_log(request=request)
    #     return DetailResponse(data=result,msg="获取成功")


class LoginTokenSerializer(TokenObtainPairSerializer):
    """
    登录的序列化器:
    """

    class Meta:
        model = Users
        fields = "__all__"
        read_only_fields = ["id"]

    default_error_messages = {"no_active_account": _("账号/密码不正确")}

    def validate(self, attrs):
        if not getattr(settings, "LOGIN_NO_CAPTCHA_AUTH", False):
            return {"code": 4000, "msg": "该接口暂未开通!", "data": None}
        data = super().validate(attrs)
        data["name"] = self.user.name
        data["userId"] = self.user.id
        return {"code": 2000, "msg": "请求成功", "data": data}


class LoginTokenView(TokenObtainPairView):
    """
    登录获取token接口
    """

    serializer_class = LoginTokenSerializer
    permission_classes = []


class LogoutView(APIView):
    def post(self, request):
        return DetailResponse(msg="注销成功")


class ApiLoginSerializer(CustomModelSerializer):
    """接口文档登录-序列化器"""

    username = serializers.CharField()
    password = serializers.CharField()

    class Meta:
        model = Users
        fields = ["username", "password"]


class ApiLogin(APIView):
    """接口文档的登录接口"""

    serializer_class = ApiLoginSerializer
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user_obj = auth.authenticate(
            request,
            username=username,
            password=hashlib.md5(password.encode(encoding="UTF-8")).hexdigest(),
        )
        if user_obj:
            login(request, user_obj)
            return redirect("/")
        else:
            return ErrorResponse(msg="账号/密码错误")
