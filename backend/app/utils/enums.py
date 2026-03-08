from enum import StrEnum


class RoleEnum(StrEnum):
    ADMIN = 'admin'


class ProjectTypeEnum(StrEnum):
    WEB = 'web'
    APP = 'app'
    PROGRAM = 'program'
    AUTOMATION = 'automation'
    CRAWLER = 'crawler'
    CONTENT = 'content'
    INTERNAL_TOOL = 'internal_tool'
    DATA_PIPELINE = 'data_pipeline'
    EXPERIMENT = 'experiment'


class DomainTypeEnum(StrEnum):
    STOCK = 'stock'
    INSURANCE = 'insurance'
    BLOG = 'blog'
    REVIEW = 'review'
    SHORTS = 'shorts'
    AUTOMATION = 'automation'
    PARENTING = 'parenting'
    GENERAL_INFO = 'general_info'
    OTHER = 'other'


class ProjectStatusEnum(StrEnum):
    IDEA = 'idea'
    PLANNING = 'planning'
    DEVELOPING = 'developing'
    TESTING = 'testing'
    ACTIVE = 'active'
    AUTOMATED = 'automated'
    PAUSED = 'paused'
    DONE = 'done'
    ARCHIVED = 'archived'


class PriorityEnum(StrEnum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


class MonetizationTypeEnum(StrEnum):
    DIRECT = 'direct'
    INDIRECT = 'indirect'
    EXPERIMENTAL = 'experimental'
    INTERNAL = 'internal'


class TaskStatusEnum(StrEnum):
    TODO = 'todo'
    DOING = 'doing'
    WAITING = 'waiting'
    DONE = 'done'
    DROPPED = 'dropped'


class RelationTypeEnum(StrEnum):
    DEPENDS_ON = 'depends_on'
    USES_DATA_FROM = 'uses_data_from'
    OUTPUTS_TO = 'outputs_to'
    SHARES_MODULE_WITH = 'shares_module_with'
    PROMOTES = 'promotes'
    FEEDS = 'feeds'
    MONETIZES_WITH = 'monetizes_with'
    RELATED_TO = 'related_to'


class NoteTypeEnum(StrEnum):
    MEETING = 'meeting'
    IDEA = 'idea'
    DECISION = 'decision'
    ISSUE = 'issue'
    LOG = 'log'
