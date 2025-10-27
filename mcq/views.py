"""
MCQ (听力选择题) 视图
"""
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count, Exists, OuterRef
from exam.models import ExamModule
import random

from common.response import ApiResponse
from common.mixins import ResponseMixin
from .models import McqMaterial, McqQuestion, McqChoice, McqResponse
from .serializers import (
    McqQuestionSerializer,
    McqQuestionDetailSerializer,
    McqChoiceSerializer,
    McqResponseSerializer,
    McqMaterialWithQuestionsSerializer,
    McqResponseCreateSerializer
)


class McqPagination(PageNumberPagination):
    """MCQ分页类"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


# ==================== McqQuestion 视图 ====================

class McqQuestionsView(APIView, ResponseMixin):
    """
    获取MCQ题目
    
    支持两种模式：
    1. 按模块获取：GET /api/mcq/questions?id=1
    2. 随机模块：GET /api/mcq/questions?mode=random
    
    返回格式：
    {
        "module": {
            "id": 1,
            "title": "Part 1 - 听力理解",
            "question_count": 15
        },
        "materials": [
            {
                "id": 1,
                "title": "材料标题",
                "audio_url": "...",
                "questions": [...]
            }
        ]
    }
    
    参数：
    - id: ExamModule的ID（指定模块）
    - mode: random（随机选择一个模块）
    - 如果两个参数都不提供，返回所有启用的材料（旧版兼容）
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        module_id = request.query_params.get('id')
        mode = request.query_params.get('mode')
        
        # 新逻辑：按模块获取或随机模块
        if module_id or mode == 'random':
            return self._get_module_questions(request, module_id, mode)
        
        # 旧逻辑：兼容原来的接口（获取所有材料）
        return self._get_all_materials(request)
    
    def _get_module_questions(self, request, module_id=None, mode=None):
        """获取指定模块或随机模块的所有材料和题目"""
        
        # 获取模块
        if module_id:
            # 按ID获取指定模块
            try:
                module = ExamModule.objects.get(
                    id=module_id,
                    module_type='LISTENING_MCQ',
                    is_activate=True
                )
            except ExamModule.DoesNotExist:
                return self.error_response(message='模块不存在或未启用')
        elif mode == 'random':
            # 随机选择一个模块
            modules = ExamModule.objects.filter(
                module_type='LISTENING_MCQ',
                is_activate=True
            )
            
            if not modules.exists():
                return self.error_response(message='没有可用的听力理解模块')
            
            # 随机选择
            module = random.choice(list(modules))
        else:
            return self.error_response(message='请提供id参数或设置mode=random')
        
        # 获取模块关联的所有材料
        materials = module.mcq_materials.filter(is_enabled=True).order_by('display_order', 'created_at')
        
        # 序列化材料和题目
        materials_data = []
        total_questions = 0
        
        for material in materials:
            # 获取该材料下的所有题目
            questions = material.questions.all().prefetch_related('choices')
            question_count = questions.count()
            total_questions += question_count
            
            # 序列化题目
            questions_serializer = McqQuestionDetailSerializer(
                questions,
                many=True,
                context={'request': request}
            )
            
            materials_data.append({
                'id': material.id,
                'title': material.title,
                'description': material.description,
                'audio_url': material.audio_asset.get_file_url() if material.audio_asset else None,
                'difficulty': material.difficulty,
                'display_order': material.display_order,
                'question_count': question_count,
                'questions': questions_serializer.data
            })
        
        return self.success_response(
            data={
                'module': {
                    'id': module.id,
                    'title': module.title or f'模块 {module.id}',
                    'display_order': module.display_order,
                    'duration': module.duration,
                    'score': module.score,
                    'question_count': total_questions
                },
                'materials_count': len(materials_data),
                'total_questions': total_questions,
                'materials': materials_data
            },
            message='查询成功'
        )
    
    def _get_all_materials(self, request):
        """旧版接口：获取所有启用的材料（兼容性保留）"""
        mode = request.query_params.get('mode', 'sequential')
        count = request.query_params.get('count')
        difficulty = request.query_params.get('difficulty')

        # 获取所有启用的材料
        materials_queryset = McqMaterial.objects.filter(is_enabled=True).prefetch_related(
            'questions',
            'questions__choices'
        )
        
        # 难度筛选
        if difficulty:
            materials_queryset = materials_queryset.filter(difficulty=difficulty)
        
        # 根据模式排序或随机
        if mode == 'sequential':
            materials_queryset = materials_queryset.order_by('display_order', 'created_at')
        else:
            # 随机模式：转为列表并打乱
            materials_list = list(materials_queryset)
            random.shuffle(materials_list)
            materials_queryset = materials_list
        
        # 限制数量
        if count:
            count = int(count)
            materials_queryset = materials_queryset[:count] if hasattr(materials_queryset, '__getitem__') else list(materials_queryset)[:count]
        
        # 序列化材料（包含问题）
        materials_serializer = McqMaterialWithQuestionsSerializer(
            materials_queryset,
            many=True,
            context={'request': request}
        )
        
        # 获取独立题目（没有关联材料的）
        independent_questions = McqQuestion.objects.filter(
            material__isnull=True
        ).prefetch_related('choices')
        
        if mode == 'random':
            independent_list = list(independent_questions)
            random.shuffle(independent_list)
            independent_questions = independent_list
        
        # 序列化独立题目
        independent_serializer = McqQuestionDetailSerializer(
            independent_questions,
            many=True,
            context={'request': request}
        )
        
        # 统计总题目数
        total_questions = sum(m['question_count'] for m in materials_serializer.data) + len(independent_serializer.data)
        
        return self.success_response(
            data={
                'mode': mode,
                'materials_count': len(materials_serializer.data),
                'total_questions': total_questions,
                'materials': materials_serializer.data,
                'independent_questions': independent_serializer.data
            },
            message='查询成功'
        )


class McqQuestionsAllView(APIView, ResponseMixin):
    """
    获取所有听力理解模块及用户答题情况（包含完整的材料、问题、选项）
    
    GET /api/mcq/questions/all/ 或 /api/mcq/question/all/
    
    答题进度统计逻辑：模块ID + 用户ID + 材料ID
    
    注意：题目只能通过材料关联到模块，不再支持独立题目
    
    返回格式：
    {
        "is_authenticated": true,
        "modules": [
            {
                "id": 1,
                "title": "Part 1 - 听力理解",
                "question_count": 15,
                "answered_count": 5,
                "correct_count": 4,
                "progress": 33.3,
                "accuracy": 80.0,
                "duration": 600000,
                "score": 100,
                "materials": [
                    {
                        "id": 1,
                        "title": "机场天气广播",
                        "audio_url": "...",
                        "difficulty": "medium",
                        "question_count": 5,
                        "answered_count": 3,
                        "correct_count": 2,
                        "progress": 60.0,
                        "accuracy": 66.7,
                        "questions": [
                            {
                                "id": 1,
                                "text_stem": "...",
                                "choices": [...]
                            }
                        ]
                    }
                ]
            }
        ],
        "total_modules": 3,
        "total_questions": 45,
        "total_answered": 20,
        "total_correct": 15,
        "overall_progress": 44.4,
        "overall_accuracy": 75.0
    }
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        user = request.user
        
        # 获取所有听力理解类型的模块
        mcq_modules = ExamModule.objects.filter(
            module_type='LISTENING_MCQ',
            is_activate=True
        ).prefetch_related('mcq_materials')

        modules_data = []
        total_questions = 0
        total_answered = 0
        total_correct = 0
        
        # 检查用户是否已登录
        is_authenticated = user.is_authenticated
        
        for module in mcq_modules:
            # 先获取该模块关联的所有材料
            materials = module.mcq_materials.filter(is_enabled=True).order_by('display_order', 'created_at')
            
            # 收集所有材料下的题目ID（用于统计答题情况）
            all_question_ids = []
            materials_data = []
            
            for material in materials:
                # 获取该材料下的所有题目
                questions = material.questions.all().prefetch_related('choices')
                question_ids = list(questions.values_list('id', flat=True))
                all_question_ids.extend(question_ids)
                
                material_question_count = questions.count()
                
                # 为每个材料单独统计答题情况（模块ID + 用户ID + 材料ID）
                material_answered_count = 0
                material_correct_count = 0
                
                if is_authenticated and material_question_count > 0:
                    # 获取用户在当前模块、当前材料下的答题记录，按题目分组取最近一次
                    answered_questions = set()
                    correct_questions = set()
                    
                    for question_id in question_ids:
                        # 获取该题目的最近一次答题记录
                        latest_response = McqResponse.objects.filter(
                            user=user,
                            module=module,
                            question_id=question_id
                        ).order_by('-created_at').first()
                        
                        if latest_response:
                            answered_questions.add(question_id)
                            if latest_response.is_correct:
                                correct_questions.add(question_id)
                    
                    material_answered_count = len(answered_questions)
                    material_correct_count = len(correct_questions)

                # 计算材料级别的进度和正确率
                material_progress = round((material_answered_count / material_question_count * 100), 1) if material_question_count > 0 else 0
                material_accuracy = round((material_correct_count / material_answered_count * 100), 1) if material_answered_count > 0 else 0
                
                # 序列化题目
                questions_serializer = McqQuestionDetailSerializer(
                    questions,
                    many=True,
                    context={'request': request}
                )
                
                materials_data.append({
                    'id': material.id,
                    'title': material.title,
                    'description': material.description,
                    'audio_url': material.audio_asset.get_file_url() if material.audio_asset else None,
                    'difficulty': material.difficulty,
                    'display_order': material.display_order,
                    'question_count': material_question_count,
                    'answered_count': material_answered_count,
                    'correct_count': material_correct_count,
                    'progress': material_progress,
                    'accuracy': material_accuracy,
                    'questions': questions_serializer.data
                })
            
            # 注意：现在题目只能通过材料关联到模块，不再支持独立题目
            
            # 统计题目总数
            question_count = len(all_question_ids)
            
            if question_count == 0:
                continue
            
            # 只有登录用户才查询答题记录（按题目分组取最近一次）
            answered_count = 0
            correct_count = 0
            
            if is_authenticated and question_count > 0:
                # 按题目分组，获取每道题的最近一次答题记录
                answered_questions_set = set()
                correct_questions_set = set()
                
                for question_id in all_question_ids:
                    # 获取该题目的最近一次答题记录
                    latest_response = McqResponse.objects.filter(
                        user=user,
                        module=module,
                        question_id=question_id
                    ).order_by('-created_at').first()
                    
                    if latest_response:
                        answered_questions_set.add(question_id)
                        if latest_response.is_correct:
                            correct_questions_set.add(question_id)
                
                answered_count = len(answered_questions_set)
                correct_count = len(correct_questions_set)
            
            # 计算进度和正确率
            progress = round((answered_count / question_count * 100), 1) if question_count > 0 else 0
            accuracy = round((correct_count / answered_count * 100), 1) if answered_count > 0 else 0
            
            modules_data.append({
                'id': module.id,
                'title': module.title or f'模块 {module.id}',
                'display_order': module.display_order or 0,
                'question_count': question_count,
                'answered_count': answered_count,
                'correct_count': correct_count,
                'progress': progress,
                'accuracy': accuracy,
                'duration': module.duration,
                'score': module.score,
                'materials': materials_data
            })
            
            total_questions += question_count
            total_answered += answered_count
            total_correct += correct_count
        
        # 按显示顺序排序
        modules_data.sort(key=lambda x: x['display_order'])
        
        # 计算总体统计
        overall_progress = round((total_answered / total_questions * 100), 1) if total_questions > 0 else 0
        overall_accuracy = round((total_correct / total_answered * 100), 1) if total_answered > 0 else 0
        
        return self.success_response(
            data={
                'is_authenticated': is_authenticated,
                'modules': modules_data,
                'total_modules': len(modules_data),
                'total_questions': total_questions,
                'total_answered': total_answered,
                'total_correct': total_correct,
                'overall_progress': overall_progress,
                'overall_accuracy': overall_accuracy
            },
            message='查询成功' if is_authenticated else '查询成功（未登录用户无答题记录）'
        )


class McqSubmitAnswerView(APIView, ResponseMixin):
    """
    提交MCQ答题
    
    POST /api/mcq/submit/
    
    请求体：
    {
        "question_id": 1,
        "selected_choice_id": 2,
        "module_id": 1,  // 可选：指定所属模块ID
        "mode_type": "practice",  // practice 或 exam
        "is_timeout": false
    }
    
    返回：
    {
        "is_correct": true,
        "correct_choice": "A",
        "selected_choice": "A",
        "explanation": "..."
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        question_id = request.data.get('question_id')
        selected_choice_id = request.data.get('choice_id')
        module_id = request.data.get('module_id')
        mode_type = request.data.get('mode_type', 'practice')
        is_timeout = request.data.get('is_timeout', False)
        
        # 验证参数
        if not question_id:
            return self.error_response(message='缺少参数: question_id')
        
        try:
            question = McqQuestion.objects.get(id=question_id)
        except McqQuestion.DoesNotExist:
            return self.error_response(message='题目不存在')
        
        # 获取选中的选项和正确答案
        selected_choice = None
        is_correct = False
        
        if selected_choice_id:
            try:
                selected_choice = McqChoice.objects.get(
                    id=selected_choice_id,
                    question=question
                )
                is_correct = selected_choice.is_correct
            except McqChoice.DoesNotExist:
                return self.error_response(message='选项不存在或不属于该题目')
        
        # 创建答题记录
        response = McqResponse.objects.create(
            user=user,
            question=question,
            selected_choice=selected_choice,
            is_correct=is_correct,
            mode_type=mode_type,
            is_timeout=is_timeout
        )
        
        # 关联模块（如果提供了 module_id）
        if module_id:
            try:
                module = ExamModule.objects.get(
                    id=module_id,
                    module_type='LISTENING_MCQ',
                    is_activate=True
                )
                response.module.add(module)
            except ExamModule.DoesNotExist:
                pass  # 模块不存在时忽略，不影响答题记录的保存
        else:
            # 如果没有提供 module_id，则从题目的材料获取关联的模块
            if question.material:
                modules = question.material.exam_module.filter(
                    module_type='LISTENING_MCQ',
                    is_activate=True
                )
                response.module.set(modules)
        
        # 获取正确答案
        correct_choice = question.choices.filter(is_correct=True).first()
        
        return self.success_response(
            data={
                'response_id': response.id,
                'is_correct': is_correct,
                'correct_choice': correct_choice.label if correct_choice else None,
                'selected_choice': selected_choice.label if selected_choice else None,
                'is_timeout': is_timeout
            },
            message='答题记录已保存'
        )


class McqUserProgressView(APIView, ResponseMixin):
    """
    获取用户在指定模块的答题进度
    
    GET /api/mcq/progress/{module_id}/
    
    返回：
    {
        "module": {...},
        "questions": [
            {
                "id": 1,
                "text_stem": "...",
                "is_answered": true,
                "is_correct": true,
                "last_answered_at": "..."
            }
        ]
    }
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, module_id):
        user = request.user
        
        try:
            module = ExamModule.objects.get(
                id=module_id,
                module_type='LISTENING_MCQ',
                is_activate=True
            )
        except ExamModule.DoesNotExist:
            return self.error_response(message='模块不存在')
        
        # 获取模块的所有题目（从材料获取）
        all_questions = []
        
        # 从材料获取题目
        materials = module.mcq_materials.filter(is_enabled=True)
        for material in materials:
            all_questions.extend(material.questions.all())
        
        questions_data = []
        for question in all_questions:
            # 获取用户在当前模块下的最近答题记录
            latest_response = McqResponse.objects.filter(
                user=user,
                module=module,
                question=question
            ).order_by('-answered_at').first()
            
            questions_data.append({
                'id': question.id,
                'text_stem': question.text_stem,
                'is_answered': latest_response is not None,
                'is_correct': latest_response.is_correct if latest_response else None,
                'last_answered_at': latest_response.answered_at if latest_response else None,
                'attempt_count': McqResponse.objects.filter(user=user, module=module, question=question).count()
            })
        
        return self.success_response(
            data={
                'module': {
                    'id': module.id,
                    'title': module.title,
                    'question_count': len(all_questions)
                },
                'questions': questions_data
            },
            message='查询成功'
        )


