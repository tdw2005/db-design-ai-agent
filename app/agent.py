from __future__ import annotations

import argparse
from pathlib import Path
import textwrap

from app.config import Settings
from app.db_executor import DatabaseExecutor
from app.llm import DeepSeekClient
from app.sql_generator import DatabaseDesignGenerator, DesignArtifact


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Database Design Agent: 根据自然语言需求生成 ER 摘要、Mermaid ER 图和 MySQL 建表 SQL。"
    )
    parser.add_argument(
        "description",
        nargs="*",
        help="数据库需求描述；如果省略则会进入交互式输入。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅生成并打印 SQL，不执行数据库部署。",
    )
    parser.add_argument(
        "--output-dir",
        default="generated",
        help="生成结果输出目录，默认保存到 generated/。",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    requirement = _read_requirement(args.description)
    settings = Settings.from_env()
    generator = DatabaseDesignGenerator(DeepSeekClient(settings))
    artifact = generator.generate(requirement)
    output_dir = Path(args.output_dir)
    _persist_artifacts(output_dir, artifact)
    _print_artifact(artifact, output_dir)

    if args.dry_run:
        print("Dry run 模式：已跳过数据库执行。")
        return

    confirmed = input("是否将以上 SQL 执行到目标 MySQL 数据库？请输入 yes 确认： ").strip()
    if confirmed.lower() != "yes":
        print("已取消执行，生成结果保留在本地文件中。")
        return

    executor = DatabaseExecutor(settings)
    executor.wait_until_ready()
    executor.execute_sql(artifact.sql)
    print("SQL 已成功执行到目标数据库。")


def _read_requirement(description_parts: list[str]) -> str:
    if description_parts:
        return " ".join(description_parts).strip()

    print("请输入数据库需求描述，输入完成后按回车提交：")
    requirement = input("> ").strip()
    if not requirement:
        raise ValueError("数据库需求描述不能为空。")
    return requirement


def _persist_artifacts(output_dir: Path, artifact: DesignArtifact) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "design-summary.md").write_text(artifact.summary + "\n", encoding="utf-8")
    (output_dir / "design-er.md").write_text(artifact.mermaid + "\n", encoding="utf-8")
    (output_dir / "schema.sql").write_text(artifact.sql + "\n", encoding="utf-8")


def _print_artifact(artifact: DesignArtifact, output_dir: Path) -> None:
    separator = "=" * 80
    print(separator)
    print("ER 模型摘要")
    print(separator)
    print(textwrap.dedent(artifact.summary).strip())
    print()
    print(separator)
    print("Mermaid ER 图")
    print(separator)
    print(artifact.mermaid.strip())
    print()
    print(separator)
    print("MySQL 8.0 建表 SQL")
    print(separator)
    print(artifact.sql.strip())
    print()
    print(f"生成文件已保存到: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
