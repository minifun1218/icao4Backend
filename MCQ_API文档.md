# MCQ 听力选择题 API 文档

## 概述

MCQ（Multiple Choice Questions）听力选择题模块提供了完整的听力理解题目管理和答题功能。

## 基础URL

所有 MCQ 相关的 API 都以 `/api/mcq/` 为前缀。

---

## 1. 获取所有听力理解模块及用户答题情况

### 接口信息

- **URL**: `/api/mcq/questions/all/`
- **方法**: `GET`
- **权限**: 允许所有人访问（AllowAny）
  - 未登录用户可以查看模块列表，但答题记录为空
  - 已登录用户可以查看模块列表和个人答题记录

### 功能说明

获取系统中所有启用的听力理解模块。
- **未登录用户**: 只能看到模块基本信息，答题相关字段都为 0
- **已登录用户**: 可以看到模块基本信息和个人答题进度、正确率

### 请求示例

```http
GET /api/mcq/questions/all/
Authorization: Bearer {token}
```

### 响应示例

**已登录用户响应示例：**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "is_authenticated": true,
    "modules": [
      {
        "id": 1,
        "title": "Part 1 - 听力理解",
        "display_order": 1,
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
            "description": "关于机场天气的广播内容",
            "audio_url": "http://example.com/media/audio/weather.mp3",
            "difficulty": "medium",
            "display_order": 1,
            "question_count": 3,
            "questions": [
              {
                "id": 1,
                "text_stem": "根据广播，当前天气如何？",
                "choices": [
                  {
                    "id": 1,
                    "label": "A",
                    "content": "晴朗",
                    "is_correct": true
                  },
                  {
                    "id": 2,
                    "label": "B",
                    "content": "多云",
                    "is_correct": false
                  },
                  {
                    "id": 3,
                    "label": "C",
                    "content": "下雨",
                    "is_correct": false
                  },
                  {
                    "id": 4,
                    "label": "D",
                    "content": "下雪",
                    "is_correct": false
                  }
                ]
              }
            ]
          }
        ],
        "independent_questions": []
      }
    ],
    "total_modules": 1,
    "total_questions": 15,
    "total_answered": 5,
    "total_correct": 4,
    "overall_progress": 33.3,
    "overall_accuracy": 80.0
  }
}
```

### 响应字段说明

#### modules（模块列表）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 模块ID |
| title | string | 模块标题 |
| display_order | integer | 显示顺序 |
| question_count | integer | 模块包含的题目总数 |
| answered_count | integer | 用户已答题数 |
| correct_count | integer | 用户答对题数 |
| progress | float | 答题进度（百分比） |
| accuracy | float | 正确率（百分比） |
| duration | integer | 考试时长（毫秒） |
| score | integer | 模块分值 |
| materials | array | 听力材料列表（包含题目和选项） |
| independent_questions | array | 独立题目列表（不属于任何材料） |

#### materials 数组中每个元素

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 材料ID |
| title | string | 材料标题 |
| description | string | 材料描述 |
| audio_url | string | 音频URL |
| difficulty | string | 难度：easy/medium/hard |
| display_order | integer | 显示顺序 |
| question_count | integer | 该材料包含的题目数 |
| questions | array | 题目列表（包含选项） |

#### questions 数组中每个元素

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 题目ID |
| text_stem | string | 题干 |
| choices | array | 选项列表 |

#### choices 数组中每个元素

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 选项ID |
| label | string | 选项标签（A/B/C/D） |
| content | string | 选项内容 |
| is_correct | boolean | 是否为正确答案 |

#### 总体统计

| 字段名 | 类型 | 说明 |
|--------|------|------|
| is_authenticated | boolean | 用户是否已登录 |
| total_modules | integer | 模块总数 |
| total_questions | integer | 所有模块的题目总数 |
| total_answered | integer | 用户答题总数（未登录为0） |
| total_correct | integer | 用户答对总数（未登录为0） |
| overall_progress | float | 总体进度（百分比，未登录为0） |
| overall_accuracy | float | 总体正确率（百分比，未登录为0） |

---

## 2. 提交答题

### 接口信息

- **URL**: `/api/mcq/submit/`
- **方法**: `POST`
- **权限**: 需要登录（IsAuthenticated）

### 功能说明

提交用户对某道题目的答案，系统会自动判断对错并记录。

### 请求体

```json
{
  "question_id": 1,
  "selected_choice_id": 2,
  "mode_type": "practice",
  "is_timeout": false
}
```

### 请求参数说明

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| question_id | integer | 是 | 题目ID |
| selected_choice_id | integer | 否 | 选中的选项ID（未选择则为null） |
| mode_type | string | 否 | 答题模式：practice（练习）或 exam（考试），默认practice |
| is_timeout | boolean | 否 | 是否超时，默认false |

### 请求示例

```http
POST /api/mcq/submit-answer/
Authorization: Bearer {token}
Content-Type: application/json

{
  "question_id": 1,
  "selected_choice_id": 2,
  "mode_type": "practice",
  "is_timeout": false
}
```

### 响应示例

```json
{
  "code": 200,
  "message": "答题记录已保存",
  "data": {
    "response_id": 123,
    "is_correct": true,
    "correct_choice": "A",
    "selected_choice": "A",
    "is_timeout": false
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| response_id | integer | 答题记录ID |
| is_correct | boolean | 是否答对 |
| correct_choice | string | 正确答案的标签（A/B/C/D） |
| selected_choice | string | 用户选择的标签（A/B/C/D） |
| is_timeout | boolean | 是否超时 |

---

## 3. 获取用户在指定模块的答题进度

### 接口信息

- **URL**: `/api/mcq/progress/{module_id}/`
- **方法**: `GET`
- **权限**: 需要登录（IsAuthenticated）

### 功能说明

获取用户在指定模块中每道题的答题情况。

### 路径参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| module_id | integer | 模块ID |

### 请求示例

```http
GET /api/mcq/progress/1/
Authorization: Bearer {token}
```

### 响应示例

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "module": {
      "id": 1,
      "title": "Part 1 - 听力理解",
      "question_count": 15
    },
    "questions": [
      {
        "id": 1,
        "text_stem": "请选择正确的描述...",
        "is_answered": true,
        "is_correct": true,
        "last_answered_at": "2025-10-24T14:30:00Z",
        "attempt_count": 2
      },
      {
        "id": 2,
        "text_stem": "根据听力材料，选择...",
        "is_answered": false,
        "is_correct": null,
        "last_answered_at": null,
        "attempt_count": 0
      }
    ]
  }
}
```

### 响应字段说明

#### module（模块信息）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 模块ID |
| title | string | 模块标题 |
| question_count | integer | 题目总数 |

#### questions（题目列表）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 题目ID |
| text_stem | string | 题干 |
| is_answered | boolean | 是否已答题 |
| is_correct | boolean/null | 最近一次答题是否正确（未答题则为null） |
| last_answered_at | datetime/null | 最近答题时间 |
| attempt_count | integer | 答题次数 |

---

## 4. 获取题目

### 接口信息

- **URL**: `/api/mcq/questions`
- **方法**: `GET`
- **权限**: 允许所有人访问（AllowAny）

### 功能说明

获取听力材料和题目，支持三种模式：

#### 模式一：按模块ID获取（推荐）
获取指定模块的所有材料和题目。

**请求示例**：
```http
GET /api/mcq/questions?id=1
```

**响应示例**：
```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "module": {
      "id": 1,
      "title": "Part 1 - 听力理解",
      "display_order": 1,
      "duration": 600000,
      "score": 100,
      "question_count": 15
    },
    "materials_count": 3,
    "total_questions": 15,
    "materials": [
      {
        "id": 1,
        "title": "机场天气广播",
        "description": "关于机场天气的广播内容",
        "audio_url": "http://example.com/media/audio/weather.mp3",
        "difficulty": "medium",
        "display_order": 1,
        "question_count": 3,
        "questions": [
          {
            "id": 1,
            "text_stem": "根据广播，当前天气如何？",
            "choices": [
              {
                "id": 1,
                "label": "A",
                "content": "晴朗",
                "is_correct": true
              },
              {
                "id": 2,
                "label": "B",
                "content": "多云",
                "is_correct": false
              },
              {
                "id": 3,
                "label": "C",
                "content": "下雨",
                "is_correct": false
              },
              {
                "id": 4,
                "label": "D",
                "content": "下雪",
                "is_correct": false
              }
            ]
          }
        ]
      }
    ],
    "independent_questions": []
  }
}
```

#### 模式二：随机获取模块
随机选择一个听力理解模块并获取其所有材料和题目。

**请求示例**：
```http
GET /api/mcq/questions?mode=random
```

**响应格式**：与模式一相同，但模块是随机选择的。

#### 模式三：获取所有材料（旧版兼容）
不指定 id 或 mode=random，获取所有启用的材料（仅用于兼容旧版本）。

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 否 | ExamModule的ID（推荐使用） |
| mode | string | 否 | random（随机选择模块） |
| count | integer | 否 | 仅模式三：返回材料数量 |
| difficulty | string | 否 | 仅模式三：难度筛选 easy/medium/hard |

**参数优先级**：
- 如果提供 `id`，使用模式一（按ID获取）
- 否则如果 `mode=random`，使用模式二（随机获取）
- 否则使用模式三（旧版兼容）

### 推荐使用方式

```http
# 推荐：获取指定模块的题目
GET /api/mcq/questions?id=1

# 或：随机获取一个模块
GET /api/mcq/questions?mode=random
```

### 响应字段说明

#### 模式一和模式二响应字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| module | object | 模块信息 |
| module.id | integer | 模块ID |
| module.title | string | 模块标题 |
| module.display_order | integer | 显示顺序 |
| module.duration | integer | 考试时长（毫秒） |
| module.score | integer | 模块分值 |
| module.question_count | integer | 题目总数 |
| materials_count | integer | 材料数量 |
| total_questions | integer | 总题目数 |
| materials | array | 材料列表 |
| independent_questions | array | 独立题目列表（不属于任何材料） |

#### materials 数组中每个元素

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 材料ID |
| title | string | 材料标题 |
| description | string | 材料描述 |
| audio_url | string | 音频URL |
| difficulty | string | 难度：easy/medium/hard |
| display_order | integer | 显示顺序 |
| question_count | integer | 该材料包含的题目数 |
| questions | array | 题目列表 |

#### questions 数组中每个元素

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 题目ID |
| text_stem | string | 题干 |
| choices | array | 选项列表 |

#### choices 数组中每个元素

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 选项ID |
| label | string | 选项标签（A/B/C/D） |
| content | string | 选项内容 |
| is_correct | boolean | 是否为正确答案 |

---

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未认证（需要登录） |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 使用流程示例

### 完整流程：学生做题

#### 1. 查看所有模块

```javascript
// 获取所有模块及答题情况
GET /api/mcq/questions/all/

// 响应：
{
  "modules": [
    {"id": 1, "title": "Part 1", "question_count": 15, "progress": 33.3},
    {"id": 2, "title": "Part 2", "question_count": 20, "progress": 0}
  ]
}
```

#### 2. 选择模块获取题目

```javascript
// 方式一：选择指定模块（推荐）
GET /api/mcq/questions?id=1

// 方式二：随机选择一个模块
GET /api/mcq/questions?mode=random

// 响应：
{
  "module": {
    "id": 1,
    "title": "Part 1 - 听力理解",
    "question_count": 15,
    "duration": 600000
  },
  "materials": [
    {
      "id": 1,
      "title": "机场天气广播",
      "audio_url": "...",
      "questions": [
        {"id": 1, "text_stem": "...", "choices": [...]}
      ]
    }
  ]
}
```

#### 3. 播放音频并答题

```javascript
// 前端播放 material.audio_url
// 学生选择答案后提交

POST /api/mcq/submit/
{
  "question_id": 1,
  "selected_choice_id": 2,
  "mode_type": "practice"
}

// 响应：
{
  "is_correct": true,
  "correct_choice": "A",
  "selected_choice": "A"
}
```

#### 4. 查看进度

```javascript
// 查看模块答题进度
GET /api/mcq/progress/1/

// 或再次查看所有模块的进度
GET /api/mcq/questions/all/
```

### 快速练习流程

```javascript
// 1. 随机获取一个模块的题目
GET /api/mcq/questions?mode=random

// 2. 直接开始答题
POST /api/mcq/submit/
{
  "question_id": 1,
  "selected_choice_id": 2,
  "mode_type": "practice"
}

// 3. 继续下一题...
```

## 注意事项

1. **认证要求**：除了获取题目接口外，其他接口都需要用户登录
2. **答题记录**：每次提交都会创建新的答题记录，允许重复答题
3. **进度计算**：进度基于最近一次答题结果
4. **模块筛选**：`/questions/all/` 只返回 `module_type='LISTENING_MCQ'` 且 `is_activate=True` 的模块
5. **听力材料**：题目按听力材料分组，一段材料可以包含多道题目

