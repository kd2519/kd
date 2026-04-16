import os
import glob
import shutil
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = '清理项目中的.pyc文件和__pycache__目录'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detail',
            action='store_true',
            help='显示详细信息',
        )

    def handle(self, *args, **options):
        detail = options['detail']
        project_root = os.getcwd()
        removed_count = 0

        self.stdout.write("开始清理.pyc文件和__pycache__目录...")

        # 跳过虚拟环境和Python包目录
        skip_dirs = ['venv', '.env', '.venv', 'env', 'Lib', 'lib', 'site-packages']

        # 清理.pyc文件
        for root, dirs, files in os.walk(project_root):
            # 跳过不需要的目录
            for skip_dir in skip_dirs:
                if skip_dir in dirs:
                    dirs.remove(skip_dir)

            for file in files:
                if file.endswith('.pyc'):
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        removed_count += 1
                        if detail:
                            self.stdout.write(f'✓ 已删除: {os.path.relpath(file_path, project_root)}')
                    except Exception as e:
                        self.stderr.write(f'✗ 删除失败: {file_path} - {e}')

        # 清理__pycache__目录
        for root, dirs, files in os.walk(project_root):
            # 跳过不需要的目录
            for skip_dir in skip_dirs:
                if skip_dir in dirs:
                    dirs.remove(skip_dir)

            if '__pycache__' in dirs:
                cache_dir = os.path.join(root, '__pycache__')
                try:
                    shutil.rmtree(cache_dir)
                    removed_count += 1
                    if detail:
                        self.stdout.write(f'✓ 已删除目录: {os.path.relpath(cache_dir, project_root)}')
                except Exception as e:
                    self.stderr.write(f'✗ 删除目录失败: {cache_dir} - {e}')

        if removed_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'✓ 清理完成！共删除 {removed_count} 个文件/目录')
            )
        else:
            self.stdout.write(
                self.style.WARNING('✓ 没有找到需要清理的.pyc文件或__pycache__目录')
            )