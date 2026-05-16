from django.core.management.base import BaseCommand

from resources.models import AccessService, MissionTask, Quest, Resource, ServiceConfig

TAB_DESCRIPTIONS = {
    "focus": "Các nhiệm vụ lặp lại để tạo output cốt lõi mỗi ngày.",
    "grow": "Chuỗi hành động tăng reach, follower, và traffic về sản phẩm.",
    "maintain": "Checklist vận hành để hệ thống chạy ổn định và không bị gián đoạn.",
    "learn": "Học có hệ thống, theo chu kỳ lặp để tích lũy kỹ năng dài hạn.",
}

MISSIONS = [
    (
        "Daily Content Pipeline",
        "Tạo content hàng ngày từ signal.",
        "focus",
        "Daily",
        12,
        [
            {"title": "Chọn topic và angle trong ngày", "hint": "Lấy insight chính từ market + signal.", "requires": "trading,agentic", "links": [{"label": "Open Trading", "url": "http://trading.localhost"}, {"label": "Open Agentic AI", "url": "http://agentic.localhost"}]},
            {"title": "Viết draft bài", "hint": "Bản ngắn cho X và bản dài cho blog.", "requires": "research", "links": [{"label": "Open Research Blog", "url": "http://research.localhost"}]},
            {"title": "Lên lịch publish", "hint": "Chốt khung giờ và format kênh.", "requires": "buffer,x", "links": [{"label": "Open Buffer", "url": "https://buffer.com", "external": True}, {"label": "Open X", "url": "https://x.com", "external": True}]},
            {"title": "Review kết quả 24h", "hint": "Lưu learnings vào note hôm sau.", "requires": "x,buffer"},
        ],
    ),
    (
        "Signal Validation Loop",
        "Xác thực tín hiệu giao dịch.",
        "focus",
        "Daily",
        8,
        [
            {"title": "Scan tín hiệu mới", "requires": "trading"},
            {"title": "Cross-check intermarket", "requires": "trading,agentic"},
            {"title": "Ghi quyết định và lý do"},
        ],
    ),
    (
        "Cross-Channel Distribution",
        "Phân phối content đa kênh.",
        "grow",
        "Daily",
        9,
        [
            {"title": "Publish 1 post trên X", "requires": "x", "links": [{"label": "Open X", "url": "https://x.com", "external": True}]},
            {"title": "Đưa bài sang Hashnode hoặc Research Blog", "requires": "hashnode,research", "links": [{"label": "Open Hashnode", "url": "https://hashnode.com", "external": True}, {"label": "Open Research", "url": "http://research.localhost"}]},
            {"title": "Schedule follow-up với Buffer", "requires": "buffer", "links": [{"label": "Open Buffer", "url": "https://buffer.com", "external": True}]},
            {"title": "Ghi metric: impression, click, conversion", "requires": "x,buffer"},
        ],
    ),
    (
        "Creative IP Growth",
        "Phát triển IP sáng tạo.",
        "grow",
        "Weekly",
        14,
        [
            {"title": "Viết 1 đoạn lore hoặc script video"},
            {"title": "Update game hoặc wiki", "requires": "legacy,lore", "links": [{"label": "Open Legacy", "url": "http://legacy.localhost"}, {"label": "Open Lore", "url": "http://lucas-lore.localhost"}]},
            {"title": "Phát hành teaser lên YouTube/X", "requires": "youtube,x", "links": [{"label": "Open YouTube", "url": "https://www.youtube.com/@lucasmediavn", "external": True}]},
        ],
    ),
    (
        "Morning Ops Check",
        "Kiểm tra hệ thống hằng sáng.",
        "maintain",
        "Daily",
        7,
        [
            {"title": "Check trạng thái dịch vụ chính"},
            {"title": "Check hàng đợi Celery/worker"},
            {"title": "Review lỗi mới trong log"},
            {"title": "Update board incident nếu có"},
        ],
    ),
    (
        "Security / Backup Routine",
        "Bảo mật và backup định kỳ.",
        "maintain",
        "Weekly",
        11,
        [
            {"title": "Run security scan định kỳ", "requires": "quarks", "links": [{"label": "Open Quarks", "url": "http://quarks.localhost"}]},
            {"title": "Verify backup restore sample"},
            {"title": "Rotate secrets/token theo lịch"},
        ],
    ),
    (
        "GenAI Track",
        "Học AI/ML hàng ngày.",
        "learn",
        "Daily",
        6,
        [
            {"title": "Học 1 lesson Coursera", "requires": "coursera", "links": [{"label": "Open Coursera", "url": "https://www.coursera.org", "external": True}]},
            {"title": "Viết lại note ứng dụng thực tế"},
            {"title": "Áp dụng vào 1 project hiện có"},
        ],
    ),
    (
        "Chinese Practice",
        "Luyện tiếng Trung hàng ngày.",
        "learn",
        "Daily",
        4,
        [
            {"title": "Duolingo 10-15 phút", "requires": "duolingo", "links": [{"label": "Open Duolingo", "url": "https://www.duolingo.com", "external": True}]},
            {"title": "Review deck Anki", "requires": "anki", "links": [{"label": "Open Anki", "url": "https://apps.ankiweb.net", "external": True}]},
            {"title": "Tra 5 từ mới bằng Pleco", "requires": "pleco", "links": [{"label": "Open Pleco", "url": "https://www.pleco.com", "external": True}]},
        ],
    ),
]

RESOURCES = [
    ("Max Engine V2", "max-engine-v2", "Công cụ trading cá nhân và signal engine.", "product", "📈", "ic-blue", [{"label": "trading.localhost", "url": "http://trading.localhost", "tag": "Trading"}]),
    ("Dreamer House", "dreamer-house", "Story platform với recommendation.", "product", "📚", "ic-purple", [{"label": "dreamer.localhost", "url": "http://dreamer.localhost", "tag": "Story"}]),
    ("Agentic AI", "agentic-ai", "RAG research assistant.", "product", "🤖", "ic-green", [{"label": "agentic.localhost", "url": "http://agentic.localhost", "tag": "Research"}]),
    ("Bahang Xom", "bahang-xom", "Social listening & brand analysis.", "product", "🏪", "ic-orange", [{"label": "bahangxom.localhost", "url": "http://bahangxom.localhost", "tag": "Social"}]),
    ("OCR Portal", "ocr-portal", "Document OCR + API + MinIO.", "product", "🔍", "ic-teal", [{"label": "ocr.localhost", "url": "http://ocr.localhost", "tag": "UI"}, {"label": "ocr-api.localhost", "url": "http://ocr-api.localhost", "tag": "API"}, {"label": "ocr-minio.localhost", "url": "http://ocr-minio.localhost", "tag": "MinIO"}]),
    ("Novel Pipeline", "novel-pipeline", "Crawl, translate, và build EPUB/MOBI.", "product", "📖", "ic-yellow", [{"label": "ebook.localhost", "url": "http://ebook.localhost", "tag": "eBook"}]),
    ("Quarks", "quarks", "Security scanning + target management.", "product", "🔐", "ic-pink", [{"label": "quarks.localhost", "url": "http://quarks.localhost", "tag": "Scanner"}, {"label": "cloud.projectdiscovery.io", "url": "https://cloud.projectdiscovery.io/", "tag": "Cloud", "external": True}]),
    ("Laura Bot", "laura-bot", "Telegram bot webhook and FSM flow.", "product", "✈️", "ic-blue", [{"label": "laura.localhost", "url": "http://laura.localhost", "tag": "Bot"}]),
    ("X", "x-channel", "", "channel", "𝕏", "ic-blue", [{"label": "x.com", "url": "https://x.com", "tag": "Distribution", "external": True}]),
    ("Hashnode", "hashnode", "", "channel", "🔷", "ic-teal", [{"label": "hashnode.com", "url": "https://hashnode.com", "tag": "Blog", "external": True}]),
    ("YouTube", "youtube", "", "channel", "▶️", "ic-red", [{"label": "youtube.com/@lucasmediavn", "url": "https://www.youtube.com/@lucasmediavn", "tag": "Video", "external": True}]),
    ("Buffer", "buffer-channel", "", "channel", "📅", "ic-green", [{"label": "buffer.com", "url": "https://buffer.com", "tag": "Schedule", "external": True}]),
    ("Coursera", "coursera-channel", "", "channel", "🎓", "ic-yellow", [{"label": "coursera.org", "url": "https://www.coursera.org", "tag": "Learning", "external": True}]),
]

QUESTS = [
    ("Học tiếng Anh 10 phút", "Duolingo hoặc bất kỳ nguồn nào · mỗi ngày", "📖", "ic-blue", 1, "active"),
    ("Hoàn thành 1 bài học Coursera", "Gen AI Engineer cert · mỗi ngày", "🎓", "ic-purple", 5, "active"),
    ("Deploy 1 tính năng mới", "Bất kỳ project nào trong workspace", "🚀", "ic-green", 10, "active"),
    ("Viết 1 blog post hoặc research note", "Publish lên Research Blog", "📝", "ic-yellow", 8, "locked"),
    ("Tập thể dục 20 phút", "Bất kỳ hoạt động thể chất nào", "💪", "ic-orange", 2, "done"),
]

ACCESS_SERVICES = [
    ("Max Engine", "trading", "http://trading.localhost", False),
    ("Agentic AI", "agentic", "http://agentic.localhost", False),
    ("Research Blog", "research", "http://research.localhost", False),
    ("Buffer", "buffer", "https://buffer.com", True),
    ("X (Twitter)", "x", "https://x.com", True, [{"label": "Settings", "href": "#", "data_open_tab": "settings"}]),
    ("Hashnode", "hashnode", "https://hashnode.com", True),
    ("YouTube", "youtube", "https://www.youtube.com/@lucasmediavn", True),
    ("Legacy of Lucas", "legacy", "http://legacy.localhost", False),
    ("Lucas Lore", "lore", "http://lucas-lore.localhost", False),
    ("Quarks", "quarks", "http://quarks.localhost", False),
    ("Coursera", "coursera", "https://www.coursera.org", True),
    ("Duolingo", "duolingo", "https://www.duolingo.com", True),
    ("Anki", "anki", "https://apps.ankiweb.net", True),
    ("Pleco", "pleco", "https://www.pleco.com", True),
]

SERVICE_CONFIGS = [
    ("x", "oauth", {"scope": "tweet.read tweet.write users.read"}),
    ("buffer", "oauth", {}),
]


class Command(BaseCommand):
    help = "Seed all dashboard data (missions, resources, quests, access services)"

    def handle(self, *args, **options):
        for title, desc, tab, repeat, reward, steps in MISSIONS:
            MissionTask.objects.get_or_create(
                title=title,
                defaults={
                    "description": desc,
                    "meta": {
                        "tab": tab,
                        "repeat": repeat,
                        "reward": reward,
                        "steps": steps,
                    },
                },
            )

        for name, slug, desc, category, icon, icon_class, links in RESOURCES:
            Resource.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "description": desc,
                    "category": category,
                    "icon": icon,
                    "icon_class": icon_class,
                    "links": links,
                },
            )

        for title, desc, icon, icon_class, reward, status in QUESTS:
            Quest.objects.get_or_create(
                title=title,
                defaults={
                    "description": desc,
                    "icon": icon,
                    "icon_class": icon_class,
                    "reward": reward,
                    "status": status,
                },
            )

        for item in ACCESS_SERVICES:
            name, slug, url, is_external = item[:4]
            extra_links = item[4] if len(item) > 4 else []
            AccessService.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "url": url,
                    "is_external": is_external,
                    "extra_links": extra_links,
                },
            )

        for name, stype, settings in SERVICE_CONFIGS:
            ServiceConfig.objects.get_or_create(
                service_name=name,
                defaults={"service_type": stype, "settings": settings},
            )

        self.stdout.write(self.style.SUCCESS("Seeded all dashboard data."))
