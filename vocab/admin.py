"""
Vocab Admin 配置
"""
from django.contrib import admin
from .models import AvVocabTopic, AvVocab, UserVocabLearning, UserTermLearning


@admin.register(AvVocabTopic)
class AvVocabTopicAdmin(admin.ModelAdmin):
    """航空词汇主题Admin"""
    list_display = ['id', 'code', 'name_zh', 'name_en', 'display_order', 'created_at']
    list_filter = ['created_at']
    search_fields = ['code', 'name_zh', 'name_en']
    ordering = ['display_order', 'id']


@admin.register(AvVocab)
class AvVocabAdmin(admin.ModelAdmin):
    """航空词汇Admin"""
    list_display = ['id', 'headword', 'ipa', 'pos', 'cefr_level', 'topic', 'audio_asset', 'created_at']
    list_filter = ['cefr_level', 'pos', 'topic', 'created_at']
    search_fields = ['headword', 'lemma', 'definition_zh']
    ordering = ['-created_at']
    list_select_related = ['topic', 'audio_asset']


@admin.register(UserVocabLearning)
class UserVocabLearningAdmin(admin.ModelAdmin):
    """用户词汇学习记录Admin"""
    list_display = [
        'id', 'user', 'vocab', 'study_count', 
        'mastery_level', 'is_favorited', 'is_mastered',
        'last_learned_at'
    ]
    list_filter = [
        'mastery_level', 'is_favorited', 'is_mastered', 
        'last_learned_at', 'first_learned_at'
    ]
    search_fields = ['user__username', 'vocab__headword']
    readonly_fields = ['first_learned_at', 'last_learned_at']
    ordering = ['-last_learned_at']
    list_select_related = ['user', 'vocab']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'vocab')
        }),
        ('学习进度', {
            'fields': ('study_count', 'mastery_level', 'is_favorited', 'is_mastered')
        }),
        ('时间信息', {
            'fields': ('first_learned_at', 'last_learned_at', 'next_review_at')
        }),
        ('备注', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserTermLearning)
class UserTermLearningAdmin(admin.ModelAdmin):
    """用户术语学习记录Admin"""
    list_display = [
        'id', 'user', 'term', 'study_count', 
        'mastery_level', 'is_favorited', 'is_mastered',
        'last_learned_at'
    ]
    list_filter = [
        'mastery_level', 'is_favorited', 'is_mastered',
        'last_learned_at', 'first_learned_at'
    ]
    search_fields = ['user__username', 'term__headword']
    readonly_fields = ['first_learned_at', 'last_learned_at']
    ordering = ['-last_learned_at']
    list_select_related = ['user', 'term']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'term')
        }),
        ('学习进度', {
            'fields': ('study_count', 'mastery_level', 'is_favorited', 'is_mastered')
        }),
        ('时间信息', {
            'fields': ('first_learned_at', 'last_learned_at', 'next_review_at')
        }),
        ('备注', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
