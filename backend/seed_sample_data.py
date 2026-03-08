from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.note import Note
from app.models.project import Project
from app.models.relation import ProjectRelation
from app.models.task import Task


def run() -> None:
    with SessionLocal() as db:
        existing = db.scalar(select(Project).limit(1))
        if existing:
            print('Sample data already exists.')
            return

        p1 = Project(
            name='지지저항Lab',
            slug='support-resistance-lab',
            summary='주식 정보 및 분석 콘텐츠 웹사이트',
            project_type='web',
            domain_type='stock',
            status='active',
            priority='high',
            monetization_type='indirect',
            current_focus='홈 개편 및 블로그 카드 구조 정리',
            next_action='메인 상단 섹션 재배치',
        )
        p2 = Project(
            name='보험 기사 수집기',
            slug='insurance-news-crawler',
            summary='보험 기사 수집 및 요약 자동화',
            project_type='crawler',
            domain_type='insurance',
            status='developing',
            priority='critical',
            monetization_type='internal',
            current_focus='최근 기사 분류 규칙 보정',
            next_action='카테고리 분류 로직 보정',
            blocker='네이버 기사 구조 변경 대응 필요',
        )
        p3 = Project(
            name='건강 블로그 자동화',
            slug='health-blog-automation',
            summary='건강 키워드 기반 블로그 글 자동 생성',
            project_type='automation',
            domain_type='blog',
            status='developing',
            priority='high',
            monetization_type='indirect',
            current_focus='본문 프롬프트 템플릿 개선',
            next_action='서론/결론 품질 향상 프롬프트 적용',
        )
        db.add_all([p1, p2, p3])
        db.commit()
        db.refresh(p1)
        db.refresh(p2)
        db.refresh(p3)

        t1 = Task(project_id=p1.id, title='홈 블로그 카드 UI 수정', task_status='todo', priority='high', is_today_focus=True)
        t2 = Task(project_id=p2.id, title='기사 분류 규칙 테스트', task_status='doing', priority='critical', is_today_focus=True)
        t3 = Task(project_id=p3.id, title='건강 키워드 프롬프트 정리', task_status='waiting', priority='medium')
        db.add_all([t1, t2, t3])

        r1 = ProjectRelation(source_project_id=p2.id, target_project_id=p3.id, relation_type='outputs_to', description='보험 기사 인사이트를 블로그 초안에 활용')
        r2 = ProjectRelation(source_project_id=p3.id, target_project_id=p1.id, relation_type='promotes', description='생성된 글을 사이트 내 콘텐츠로 전환')
        db.add_all([r1, r2])

        n1 = Note(project_id=p1.id, note_type='decision', title='홈 우선순위 확정', content='차트보다 블로그 글 노출을 우선한다.')
        n2 = Note(project_id=p2.id, note_type='issue', title='구조 변경 대응 필요', content='네이버 뉴스 셀렉터 구조가 바뀌어 크롤링 규칙 수정이 필요하다.')
        db.add_all([n1, n2])
        db.commit()
        print('Sample data inserted.')


if __name__ == '__main__':
    run()
