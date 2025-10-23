"""
账号相关视图
"""
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.db.models import Count, Avg, Q

from common.response import ApiResponse
from common.mixins import ResponseMixin
from .models import WxUser, UserLearningProgress
from .serializers import (
    WxLoginSerializer, 
    WxUserSerializer, 
    UserUpdateSerializer,
    UserLearningProgressSerializer
)
from .utils import get_wechat_session


class WxLoginView(APIView):
    """
    微信小程序登录接口
    
    POST /api/account/wx-login/
    {
        "code": "微信登录返回的code",
        "username": "用户昵称（可选）",
        "avatar": "用户头像URL（可选）",
        "gender": 1  // 性别（可选）
    }
    返回:
    {
        "code": 200,
        "message": "登录成功",
        "data": {
            "access_token": "访问令牌",
            "refresh_token": "刷新令牌",
            "user": {用户信息}
        }
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):

        serializer = WxLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.bad_request(
                message='参数错误',
                data=serializer.errors
            )
        
        code = serializer.validated_data.get('code')

        username = serializer.validated_data.get('username', '')
        avatar = serializer.validated_data.get('avatar', '')
        gender = serializer.validated_data.get('gender', 0)
        
        # 1. 调用微信接口获取openid和session_key
        wx_result = get_wechat_session(code)
        if not wx_result or 'openid' not in wx_result:
            return ApiResponse.unauthorized(
                message='微信登录失败，请重试'
            )
        
        openid = wx_result['openid']
        session_key = wx_result.get('session_key', '')
        
        # 2. 查找或创建用户
        user, created = WxUser.objects.get_or_create(
            openid=openid,
            defaults={
                'username': username or f'用户{openid[-8:]}',
                'avatar': avatar,
                'gender': gender,
                'join_date': timezone.now().date(),
                'status': 1
            }
        )
        
        # 3. 如果用户已存在，更新用户信息
        if not created:
            if username:
                user.username = username
            if avatar:
                user.avatar = avatar
            if gender:
                user.gender = gender
            user.save()
        
        # 4. 生成JWT Token
        refresh = RefreshToken()
        refresh['user_id'] = user.id
        refresh['openid'] = user.openid
        refresh['username'] = user.username
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # 更新最后登录时间
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # 5. 返回token和用户信息
        user_data = WxUserSerializer(user).data
        
        return ApiResponse.success(
            message='登录成功',
            data={
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user_data
            }
        )


class UserInfoView(APIView):
    """
    获取当前用户信息
    
    GET /api/account/user-info/
    Headers: Authorization: Bearer <access_token>
    
    返回:
    {
        "code": 200,
        "message": "success",
        "data": {用户信息}
    }
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        serializer = WxUserSerializer(user)
        return ApiResponse.success(
            message='获取成功',
            data=serializer.data
        )
    
    def put(self, request):
        """
        更新用户信息
        
        PUT /api/account/user-info/
        Headers: Authorization: Bearer <access_token>
        Body: {
            "username": "新昵称",
            "phone": "手机号",
            ...
        }
        """
        user = request.user
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return ApiResponse.success(
                message='更新成功',
                data=serializer.data
            )
        
        return ApiResponse.bad_request(
            message='参数错误',
            data=serializer.errors
        )


class TokenRefreshView(APIView):
    """
    刷新Token
    
    POST /api/account/token-refresh/
    {
        "refresh_token": "刷新令牌"
    }
    
    返回新的access_token和refresh_token
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        
        if not refresh_token:
            return ApiResponse.bad_request(
                message='refresh_token不能为空'
            )
        
        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            
            return ApiResponse.success(
                message='刷新成功',
                data={
                    'access_token': access_token,
                    'refresh_token': str(refresh)
                }
            )
        except Exception as e:
            return ApiResponse.unauthorized(
                message='Token无效或已过期'
            )


class UserStatsView(APIView, ResponseMixin):
    """
    用户学习统计接口
    
    GET /api/auth/stats/ - 获取用户学习统计数据
    返回简洁的统计信息，用于首页或个人中心展示
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """获取用户学习统计"""
        user = request.user
        
        # 导入Response模型
        from mcq.models import McqResponse
        from lsa.models import LsaResponse
        from story.models import RetellResponse
        from opi.models import OpiResponse
        from atc.models import AtcTurnResponse
        
        # 获取学习进度记录（如果存在）
        try:
            progress = UserLearningProgress.objects.get(user=user)
            total_study_time = progress.total_study_time
            continuous_days = progress.continuous_days
            last_study_date = progress.last_study_date
        except UserLearningProgress.DoesNotExist:
            total_study_time = 0
            continuous_days = 0
            last_study_date = None
        
        # 统计总完成数
        mcq_count = McqResponse.objects.filter(user=user).count()
        lsa_count = LsaResponse.objects.filter(user=user).count()
        story_count = RetellResponse.objects.filter(user=user).count()
        opi_count = OpiResponse.objects.filter(user=user).count()
        atc_count = AtcTurnResponse.objects.filter(user=user).count()
        total_completed = mcq_count + lsa_count + story_count + opi_count + atc_count
        
        # 统计训练和考试次数
        practice_count = (
            McqResponse.objects.filter(user=user, mode_type='practice').count() +
            LsaResponse.objects.filter(user=user, mode_type='practice').count() +
            RetellResponse.objects.filter(user=user, mode_type='practice').count() +
            OpiResponse.objects.filter(user=user, mode_type='practice').count() +
            AtcTurnResponse.objects.filter(user=user, mode_type='practice').count()
        )
        
        exam_count = (
            McqResponse.objects.filter(user=user, mode_type='exam').count() +
            LsaResponse.objects.filter(user=user, mode_type='exam').count() +
            RetellResponse.objects.filter(user=user, mode_type='exam').count() +
            OpiResponse.objects.filter(user=user, mode_type='exam').count() +
            AtcTurnResponse.objects.filter(user=user, mode_type='exam').count()
        )
        
        # MCQ正确率
        mcq_correct = McqResponse.objects.filter(user=user, is_correct=True).count()
        mcq_total = McqResponse.objects.filter(user=user).count()
        mcq_accuracy = round((mcq_correct / mcq_total * 100) if mcq_total > 0 else 0, 2)
        
        # 平均分统计
        story_avg = RetellResponse.objects.filter(
            user=user, score__isnull=False
        ).aggregate(avg=Avg('score'))['avg'] or 0
        
        opi_avg = OpiResponse.objects.filter(
            user=user, score__isnull=False
        ).aggregate(avg=Avg('score'))['avg'] or 0
        
        atc_avg = AtcTurnResponse.objects.filter(
            user=user, score__isnull=False
        ).aggregate(avg=Avg('score'))['avg'] or 0
        
        # 各模块完成数
        module_stats = {
            'mcq': mcq_count,
            'lsa': lsa_count,
            'story': story_count,
            'opi': opi_count,
            'atc': atc_count
        }
        
        stats_data = {
            'user_info': {
                'id': user.id,
                'username': user.username,
                'level': user.level,
                'avatar_url': user.get_avatar_url(),
            },
            'overview': {
                'total_completed': total_completed,
                'total_study_time': total_study_time,
                'continuous_days': continuous_days,
                'last_study_date': last_study_date,
            },
            'activity': {
                'practice_count': practice_count,
                'exam_count': exam_count,
            },
            'performance': {
                'mcq_accuracy': mcq_accuracy,
                'story_avg_score': round(story_avg, 2) if story_avg else 0,
                'opi_avg_score': round(opi_avg, 2) if opi_avg else 0,
                'atc_avg_score': round(atc_avg, 2) if atc_avg else 0,
            },
            'module_stats': module_stats
        }
        
        return self.success_response(
            data=stats_data,
            message='获取学习统计成功'
        )


class UserLearningProgressView(APIView, ResponseMixin):
    """
    用户学习进度视图
    
    GET /api/auth/learning-progress/ - 获取学习进度
    POST /api/auth/learning-progress/ - 更新学习进度（自动计算）
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """获取用户学习进度"""
        user = request.user
        
        # 获取或创建进度记录
        progress, created = UserLearningProgress.objects.get_or_create(
            user=user,
            defaults=self._calculate_progress(user)
        )
        
        # 如果不是新创建的，检查是否需要更新
        if not created:
            # 可以添加缓存逻辑，避免频繁计算
            pass
        
        serializer = UserLearningProgressSerializer(progress)
        return self.success_response(
            data=serializer.data,
            message='获取学习进度成功'
        )
    
    def post(self, request):
        """
        更新学习进度（重新计算）
        可以传递 study_time 参数来累加学习时长
        """
        user = request.user
        study_time = request.data.get('study_time', 0)  # 本次学习时长（分钟）
        
        # 计算最新进度
        progress_data = self._calculate_progress(user)
        
        # 获取或更新进度记录
        progress, created = UserLearningProgress.objects.update_or_create(
            user=user,
            defaults=progress_data
        )
        
        # 累加学习时长
        if study_time > 0:
            progress.total_study_time += int(study_time)
        
        # 更新连续学习天数
        progress.update_continuous_days()
        progress.save()
        
        serializer = UserLearningProgressSerializer(progress)
        return self.success_response(
            data=serializer.data,
            message='学习进度更新成功'
        )
    
    def _calculate_progress(self, user):
        """计算用户的学习进度"""
        from mcq.models import McqResponse, McqQuestion
        from lsa.models import LsaResponse, LsaQuestion
        from story.models import RetellResponse, RetellItem
        from opi.models import OpiResponse, OpiQuestion
        from atc.models import AtcTurnResponse, AtcTurn
        
        # MCQ统计
        mcq_total = McqQuestion.objects.count()
        mcq_completed = McqResponse.objects.filter(user=user).values('question').distinct().count()
        mcq_correct = McqResponse.objects.filter(user=user, is_correct=True).count()
        mcq_practice = McqResponse.objects.filter(user=user, mode_type='practice').count()
        mcq_exam = McqResponse.objects.filter(user=user, mode_type='exam').count()
        
        # LSA统计
        lsa_total = LsaQuestion.objects.count()
        lsa_completed = LsaResponse.objects.filter(user=user).values('question').distinct().count()
        lsa_practice = LsaResponse.objects.filter(user=user, mode_type='practice').count()
        lsa_exam = LsaResponse.objects.filter(user=user, mode_type='exam').count()
        
        # Story统计
        story_total = RetellItem.objects.count()
        story_completed = RetellResponse.objects.filter(user=user).values('retell_item').distinct().count()
        story_avg = RetellResponse.objects.filter(
            user=user, score__isnull=False
        ).aggregate(avg=Avg('score'))['avg'] or 0
        story_practice = RetellResponse.objects.filter(user=user, mode_type='practice').count()
        story_exam = RetellResponse.objects.filter(user=user, mode_type='exam').count()
        
        # OPI统计
        opi_total = OpiQuestion.objects.count()
        opi_completed = OpiResponse.objects.filter(user=user).values('question').distinct().count()
        opi_avg = OpiResponse.objects.filter(
            user=user, score__isnull=False
        ).aggregate(avg=Avg('score'))['avg'] or 0
        opi_practice = OpiResponse.objects.filter(user=user, mode_type='practice').count()
        opi_exam = OpiResponse.objects.filter(user=user, mode_type='exam').count()
        
        # ATC统计
        atc_total = AtcTurn.objects.count()
        atc_completed = AtcTurnResponse.objects.filter(user=user).values('atc_turn').distinct().count()
        atc_avg = AtcTurnResponse.objects.filter(
            user=user, score__isnull=False
        ).aggregate(avg=Avg('score'))['avg'] or 0
        atc_practice = AtcTurnResponse.objects.filter(user=user, mode_type='practice').count()
        atc_exam = AtcTurnResponse.objects.filter(user=user, mode_type='exam').count()
        
        # 总计
        total_practice = mcq_practice + lsa_practice + story_practice + opi_practice + atc_practice
        total_exam = mcq_exam + lsa_exam + story_exam + opi_exam + atc_exam
        
        return {
            # MCQ
            'mcq_total': mcq_total,
            'mcq_completed': mcq_completed,
            'mcq_correct': mcq_correct,
            'mcq_practice_count': mcq_practice,
            'mcq_exam_count': mcq_exam,
            # LSA
            'lsa_total': lsa_total,
            'lsa_completed': lsa_completed,
            'lsa_practice_count': lsa_practice,
            'lsa_exam_count': lsa_exam,
            # Story
            'story_total': story_total,
            'story_completed': story_completed,
            'story_avg_score': story_avg,
            'story_practice_count': story_practice,
            'story_exam_count': story_exam,
            # OPI
            'opi_total': opi_total,
            'opi_completed': opi_completed,
            'opi_avg_score': opi_avg,
            'opi_practice_count': opi_practice,
            'opi_exam_count': opi_exam,
            # ATC
            'atc_total': atc_total,
            'atc_completed': atc_completed,
            'atc_avg_score': atc_avg,
            'atc_practice_count': atc_practice,
            'atc_exam_count': atc_exam,
            # 总计
            'total_practice_count': total_practice,
            'total_exam_count': total_exam,
        }
