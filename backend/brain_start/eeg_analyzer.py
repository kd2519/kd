import os
import pandas as pd
import textwrap
from datetime import datetime
import logging
import http.client as http_client
import re
logger = logging.getLogger(__name__)
import json
# 启用详细的HTTP请求日志（仅在调试时启用）
http_client.HTTPConnection.debuglevel = 1
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

# 火山引擎SDK模拟
try:
    from volcenginesdkarkruntime import Ark
except ImportError:
    class Ark:
        def __init__(self, api_key):
            pass
            
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    class MockResponse:
                        class Choice:
                            class Message:
                                content = "<p><strong>睡眠质量评估：优秀</strong><br>深睡比例正常（约25%），浅睡阶段稳定（约30%），REM期占比合理，无明显异常脑电活动。<br><strong>健康建议</strong>：保持当前作息规律，睡前避免电子设备使用，可适当增加轻度运动。</p>"
                            message = Message()
                        choices = [Choice()]
                    return MockResponse()

class EEGAnalyzer:
    def __init__(self, file_path, api_key,historical_records=None):
        self.file_path = file_path
        self.api_key = api_key
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.historical_records = historical_records
        # 报告存储目录 - 修复：使用项目根目录下的analysis_reports目录
        # self.report_dir = os.path.join(os.path.dirname(self.file_path), 'reports')
        from django.conf import settings
        self.report_dir = os.path.join(settings.BASE_DIR, "analysis_reports")
        os.makedirs(self.report_dir, exist_ok=True)
        self.report_path = os.path.join(self.report_dir, f"report_{self.timestamp}.html")

    def analyze(self):
        try:
            logger.info(f"开始分析文件: {self.file_path}")
            
            # 验证文件存在
            if not os.path.exists(self.file_path):
                raise FileNotFoundError(f"文件不存在: {self.file_path}")

            # 加载数据（支持Excel/CSV/TXT）
            df = self._load_data()
            if df.empty:
                raise ValueError("数据加载失败或为空")
            logger.info(f"数据加载成功，共{len(df)}行")
            # 生成统计与睡眠分析
            stats = self._generate_stats(df)
            sleep_analysis = self._analyze_sleep(df)

            # 调用AI分析
            logger.info(f"正在调用AI分析: {self.api_key}")
            # logging.info(f"AI内容: {stats}")
            # logging.info(f"AI内容: {sleep_analysis}")
            
            # 构造发送给AI的完整提示
            full_prompt = textwrap.dedent(f"""
            作为睡眠专家，分析以下脑电数据：
            1. 统计数据：{stats}
            2. 睡眠阶段：{sleep_analysis}
            生成HTML报告，包含睡眠质量评估、阶段分析和健康建议。
            重要内容用<strong>加粗</strong>，问题用<span style="color:red">红色</span>标记。
            标题颜色为黑色加粗，
            """)
            
            # 记录提示内容大小
            prompt_size = len(full_prompt.encode('utf-8'))
            logger.info(f"Full prompt size: {prompt_size} bytes")
            
            ai_content = self.call_volcengine_api(
                self.api_key,
                full_prompt
            )

            # 生成完整报告
            report_content = self._generate_report(df, stats, sleep_analysis, ai_content, self.historical_records)
            with open(self.report_path, "w", encoding="utf-8") as f:
                f.write(report_content)

            return {
                'status': 'success',
                'report_content': report_content,  # 直接返回HTML内容
                'report_filename': os.path.basename(self.report_path),
                'message': f'分析完成，共处理{len(df)}条数据'
            }
            
        except FileNotFoundError as e:
            logger.error(f"文件不存在: {str(e)}")
            return {'status': 'error', 'message': f'文件不存在: {os.path.basename(self.file_path)}'}
        except Exception as e:
            logger.error(f"分析出错: {str(e)}")
            return {'status': 'error', 'message': f'分析失败: {str(e)}'}

    def _load_data(self):
        """加载数据（支持Excel/CSV/TXT）"""
        try:
            file_ext = os.path.splitext(self.file_path)[1].lower()
            logger.info(f"加载{file_ext}格式文件: {self.file_path}")
            
            if file_ext in ['.xls', '.xlsx']:
                return self._load_excel_data()
            elif file_ext == '.csv':
                return self._load_csv_data()
            elif file_ext in ['.txt', '.log']:
                return self._load_text_data()
            else:
                raise ValueError(f"不支持的文件格式: {file_ext}")
                
        except Exception as e:
            logger.error(f"数据加载错误: {str(e)}")
            return pd.DataFrame()

    def _load_excel_data(self):
        """加载Excel文件（新增支持）"""
        logger.info(f"开始加载Excel文件: {self.file_path}")
        try:
            df = pd.read_excel(self.file_path)
            df = self._fix_column_names(df)
            
            # 转换数据类型
            for col in ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df.dropna()
        except Exception as e:
            logger.error(f"Excel加载失败: {str(e)}")
            raise

    def _load_csv_data(self):
        """加载CSV文件"""
        logger.info(f"开始加载CSV文件: {self.file_path}")
        encodings = ['utf-8', 'gbk', 'utf-8-sig', 'ISO-8859-1']
        for encoding in encodings:
            try:
                df = pd.read_csv(self.file_path, encoding=encoding)
                df = self._fix_column_names(df)
                
                for col in ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                return df.dropna()
            except UnicodeDecodeError:
                continue
        raise ValueError("CSV编码错误，无法解析")

    def _load_text_data(self):
        """加载文本文件"""
        logger.info(f"开始加载文本文件: {self.file_path}")
        data = []
        with open(self.file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    if ' - ' in line:
                        timestamp, raw_data = line.split(' - ', 1)
                    else:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        raw_data = line
                    
                    data.append({
                        '时间': timestamp,
                        'Delta': self._extract_band(raw_data, 0),
                        'Theta': self._extract_band(raw_data, 1),
                        'Alpha': self._extract_band(raw_data, 2),
                        'Beta': self._extract_band(raw_data, 3),
                        'Gamma': self._extract_band(raw_data, 4),
                    })
                except Exception as e:
                    logger.warning(f"第{line_num}行解析失败: {e}")
        return pd.DataFrame(data)

    def _fix_column_names(self, df):
        """修复列名"""
        column_mapping = {
            'delta': 'Delta', 'theta': 'Theta', 'alpha': 'Alpha',
            'beta': 'Beta', 'gamma': 'Gamma',
            'time': '时间', 'timestamp': '时间', 'datetime': '时间'
        }
        df.columns = [column_mapping.get(col.lower(), col) for col in df.columns]
        return df

    def _extract_band(self, raw_data, index):
        """从原始数据行提取指定频段的值（支持 "Delta 数值" 格式）"""
        band_names = ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']
        if index >= len(band_names):
            return 0.0
        # 使用正则表达式精确匹配：频段名 + 空格 + 数字（整数或小数）
        pattern = rf'{band_names[index]}\s+(\d+\.?\d*)'
        match = re.search(pattern, raw_data, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except:
                return 0.0
        return 0.0

    def _generate_stats(self, df):
        available_columns = [col for col in ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma'] if col in df.columns]
        if not available_columns:
            return "<p>无有效数据列</p>"
        stats = df[available_columns].describe().loc[['mean', 'std', 'min', 'max']]
        html = """
        <div class='stats-section'>
            <h3>📊 数据统计概览</h3>
            <table class='stats-table_compant'>
                <thead>
                    <tr>
                        <th>频段</th>
                        <th>平均值</th>
                        <th>标准差</th>
                        <th>最小值</th>
                        <th>最大值</th>
                    </tr>
                </thead>
                <tbody>
        """
        for band in available_columns:
            html += f"""
                <tr>
                    <td><strong>{band}</strong></td>
                    <td>{stats[band]['mean']:.2f}</td>
                    <td>{stats[band]['std']:.2f}</td>
                    <td>{stats[band]['min']:.2f}</td>
                    <td>{stats[band]['max']:.2f}</td>
                </tr>
            """
        html += """
                </tbody>
            </table>
        </div>
        """
        return html

    def _analyze_sleep(self, df):
        """分析睡眠阶段"""
        available_columns = [col for col in ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma'] if col in df.columns]
        if not available_columns:
            return "<p>无有效睡眠数据</p>"
        total = df[available_columns].sum().sum()
        if total == 0:
            return "<p>无有效睡眠数据</p>"
        pct = df[available_columns].sum() / total * 100
        sleep_score = min(100, int(0.4*pct.get('Delta',0) + 0.3*pct.get('Theta',0) + 0.2*(100-pct.get('Beta',0)) + 0.1*(100-pct.get('Gamma',0))))
        quality = "优秀" if sleep_score>=80 else "良好" if sleep_score>=60 else "一般" if sleep_score>=40 else "较差"
        return f"<div class='sleep-analysis'><h3>睡眠阶段分布</h3><ul><li>深睡期(Delta): {pct.get('Delta',0):.1f}%</li><li>浅睡期(Theta): {pct.get('Theta',0):.1f}%</li><li>REM期(Alpha): {pct.get('Alpha',0):.1f}%</li><li>清醒期(Beta): {pct.get('Beta',0):.1f}%</li><li>活跃期(Gamma): {pct.get('Gamma',0):.1f}%</li></ul><div class='sleep-score'><h4>睡眠质量评分: <span style='color: {'#52c41a' if sleep_score>=60 else '#f5222d'}'>{sleep_score}/100 ({quality})</span></h4></div></div>"

    def _generate_report(self, df, stats, sleep_analysis, ai_content, historical_records=None):
        # 清理 AI 内容
        import re
        cleaned_ai_content = re.sub(r'^<!DOCTYPE.*?>', '', ai_content, flags=re.IGNORECASE)
        cleaned_ai_content = re.sub(r'^<html[^>]*>', '', cleaned_ai_content, flags=re.IGNORECASE)
        cleaned_ai_content = re.sub(r'<body[^>]*>', '', cleaned_ai_content, flags=re.IGNORECASE)
        cleaned_ai_content = re.sub(r'</body>', '', cleaned_ai_content, flags=re.IGNORECASE)
        cleaned_ai_content = re.sub(r'</html>', '', cleaned_ai_content, flags=re.IGNORECASE)
        cleaned_ai_content = re.sub(r'\n\s*\n', '\n\n', cleaned_ai_content)

        # 计算睡眠阶段百分比（用于饼图）
        available_columns = ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']
        total = df[available_columns].sum().sum()
        if total > 0:
            current_pct = {col: (df[col].sum() / total * 100) for col in available_columns}
        else:
            current_pct = {col: 0.0 for col in available_columns}

        # 计算当前睡眠质量评分（复用 _analyze_sleep 中的逻辑）
        if total > 0:
            pct_sum = df[available_columns].sum()
            total_pct = pct_sum.sum()
            if total_pct > 0:
                pct = pct_sum / total_pct * 100
                sleep_score = min(100, int(0.4 * pct.get('Delta', 0) + 0.3 * pct.get('Theta', 0) +
                                           0.2 * (100 - pct.get('Beta', 0)) + 0.1 * (100 - pct.get('Gamma', 0))))
            else:
                sleep_score = 0
        else:
            sleep_score = 0
        # 计算当前睡眠时长与效率
        if total > 0:
            # 清醒期占比 = Beta+Gamma 的能量比例
            wake_ratio = (current_pct['Beta'] + current_pct['Gamma']) / 100.0
            # 总记录时长（从 DataFrame 的时间列推算，如果没有时间列则默认为 0）
            if '时间' in df.columns:
                # 尝试解析时间列
                try:
                    time_series = pd.to_datetime(df['时间'])
                    total_seconds = (time_series.max() - time_series.min()).total_seconds()
                    total_duration_min = total_seconds / 60.0 if total_seconds > 0 else 0
                except:
                    total_duration_min = 0
            else:
                total_duration_min = 0
            wake_duration_min = total_duration_min * wake_ratio
            sleep_duration_min = total_duration_min - wake_duration_min
            sleep_efficiency = (sleep_duration_min / total_duration_min * 100) if total_duration_min > 0 else 0
        else:
            total_duration_min = sleep_duration_min = wake_duration_min = sleep_efficiency = 0

        # 保存当前指标到变量中，供后续对比使用
        current_metrics = {
            'sleep_score': sleep_score,
            'total_duration_min': round(total_duration_min, 1),
            'sleep_duration_min': round(sleep_duration_min, 1),
            'wake_duration_min': round(wake_duration_min, 1),
            'sleep_efficiency': round(sleep_efficiency, 1),
            'delta_pct': current_pct['Delta'],
            'theta_pct': current_pct['Theta'],
            'alpha_pct': current_pct['Alpha'],
            'beta_pct': current_pct['Beta'],
            'gamma_pct': current_pct['Gamma']
        }
        # 处理历史记录，构建对比数据
        compare_html = ""
        if historical_records and len(historical_records) > 0:
            # 历史评分列表（用于趋势图）
            hist_scores = []
            hist_total_duration = []
            hist_sleep_duration = []
            hist_wake_duration = []
            hist_sleep_efficiency = []
            hist_labels = []
            hist_delta = []
            hist_theta = []
            hist_alpha = []
            hist_beta = []
            hist_gamma = []

            for rec in historical_records:
                hist_scores.append(rec.get('sleep_score', 0))
                hist_total_duration.append(rec.get('total_duration_min', 0))
                hist_sleep_duration.append(rec.get('sleep_duration_min', 0))
                hist_wake_duration.append(rec.get('wake_duration_min', 0))
                hist_sleep_efficiency.append(rec.get('sleep_efficiency', 0))
                # 格式化显示时间
                start_time = rec.get('start_time')
                if start_time:
                    label = start_time.strftime('%m-%d %H:%M')
                else:
                    label = rec.get('recording_id', '')[:8]
                hist_labels.append(label)
                hist_delta.append(rec.get('delta_pct', 0))
                hist_theta.append(rec.get('theta_pct', 0))
                hist_alpha.append(rec.get('alpha_pct', 0))
                hist_beta.append(rec.get('beta_pct', 0))
                hist_gamma.append(rec.get('gamma_pct', 0))

            # 计算历史平均
            avg_score = sum(hist_scores) / len(hist_scores) if hist_scores else 0
            avg_delta = sum(hist_delta) / len(hist_delta) if hist_delta else 0
            avg_theta = sum(hist_theta) / len(hist_theta) if hist_theta else 0
            avg_alpha = sum(hist_alpha) / len(hist_alpha) if hist_alpha else 0
            avg_beta = sum(hist_beta) / len(hist_beta) if hist_beta else 0
            avg_gamma = sum(hist_gamma) / len(hist_gamma) if hist_gamma else 0
            avg_total_duration = sum(hist_total_duration) / len(hist_total_duration) if hist_total_duration else 0
            avg_sleep_duration = sum(hist_sleep_duration) / len(hist_sleep_duration) if hist_sleep_duration else 0
            avg_wake_duration = sum(hist_wake_duration) / len(hist_wake_duration) if hist_wake_duration else 0
            avg_sleep_efficiency = sum(hist_sleep_efficiency) / len(hist_sleep_efficiency) if hist_sleep_efficiency else 0
            # 对比表格行
            compare_rows = f"""
                <tr>
                    <td><strong>当前</strong></td>
                    <td>{sleep_score:.1f}</td>
                    <td>{current_metrics['total_duration_min']:.1f} min</td>
                    <td>{current_metrics['sleep_duration_min']:.1f} min</td>
                    <td>{current_metrics['wake_duration_min']:.1f} min</td>
                    <td>{current_metrics['sleep_efficiency']:.1f}%</td>
                    <td>{current_pct['Delta']:.1f}%</td>
                    <td>{current_pct['Theta']:.1f}%</td>
                    <td>{current_pct['Alpha']:.1f}%</td>
                    <td>{current_pct['Beta']:.1f}%</td>
                    <td>{current_pct['Gamma']:.1f}%</td>
                </tr>
                <tr style="background-color: rgba(255,255,255,0.1);">
                    <td><strong>历史平均<br>({len(historical_records)}次)</strong></td>
                    <td>{avg_score:.1f}</td>
                    <td>{avg_total_duration:.1f} min</td>
                    <td>{avg_sleep_duration:.1f} min</td>
                    <td>{avg_wake_duration:.1f} min</td>
                    <td>{avg_sleep_efficiency:.1f}%</td>
                    <td>{avg_delta:.1f}%</td>
                    <td>{avg_theta:.1f}%</td>
                    <td>{avg_alpha:.1f}%</td>
                    <td>{avg_beta:.1f}%</td>
                    <td>{avg_gamma:.1f}%</td>
                </tr>
            """

            # 计算改善情况
            score_change = sleep_score - avg_score
            efficiency_change = current_metrics['sleep_efficiency'] - avg_sleep_efficiency
            sleep_duration_change = current_metrics['sleep_duration_min'] - avg_sleep_duration
            wake_duration_change = current_metrics['wake_duration_min'] - avg_wake_duration
            # 原有阶段性差值
            delta_change = current_pct['Delta'] - avg_delta
            theta_change = current_pct['Theta'] - avg_theta
            alpha_change = current_pct['Alpha'] - avg_alpha
            beta_change = current_pct['Beta'] - avg_beta
            gamma_change = current_pct['Gamma'] - avg_gamma

            improve_text = f"""
                <span style='color:{'#52c41a' if score_change > 5 else '#faad14' if score_change > 0 else '#f5222d'}'>
                    睡眠评分 {('+' if score_change >= 0 else '')}{score_change:.1f}分
                </span><br>
                <span style='color:{'#52c41a' if efficiency_change > 5 else '#faad14' if efficiency_change > 0 else '#f5222d'}'>
                    睡眠效率 {('+' if efficiency_change >= 0 else '')}{efficiency_change:.1f}%
                </span><br>
                <span>睡眠时长 {sleep_duration_change:+.1f} 分钟</span><br>
                <span>清醒时长 {wake_duration_change:+.1f} 分钟</span><br>
                <span>深睡期 {delta_change:+.1f}%</span>　<span>浅睡期 {theta_change:+.1f}%</span>　<span>REM期 {alpha_change:+.1f}%</span>
            """

            compare_html = f"""
                <div class="section_compant">
                    <h2 class='biaoti'>📈 历史对比分析</h2>
                    <div style="margin-bottom:20px;">
                        <p><strong>改善评估：</strong> {improve_text}</p>
                        <p><strong>当前评分 vs 历史平均：</strong> {sleep_score:.1f} vs {avg_score:.1f} 
                        ({'+' if score_change >= 0 else ''}{score_change:.1f}分)</p>
                    </div>
                    <div id="scoreTrendChart" style="width:100%; height:400px; margin-bottom:30px;"></div>
                    <div id="stageCompareChart" style="width:100%; height:400px; margin-bottom:20px;"></div>
                    <table class="stats-table_compant" style="margin-top:20px;">
                        <thead>
                            <tr>
                                <th>对比项</th>
                                <th>睡眠评分</th>
                                <th>总时长(min)</th>
                                <th>睡眠时长(min)</th>
                                <th>清醒时长(min)</th>
                                <th>睡眠效率(%)</th>
                                <th>深睡期%</th>
                                <th>浅睡期%</th>
                                <th>REM期%</th>
                                <th>清醒期%</th>
                                <th>活跃期%</th>
                            </tr>
                        </thead>
                        <tbody>
                            {compare_rows}
                        </tbody>
                    </table>
                </div>
                """

            # 添加 ECharts 脚本：历史评分折线图 和 阶段对比柱状图
            hist_labels_json = json.dumps(hist_labels)
            hist_scores_json = json.dumps(hist_scores)
            current_score_json = sleep_score
            hist_delta_json = json.dumps(hist_delta)
            hist_theta_json = json.dumps(hist_theta)
            hist_alpha_json = json.dumps(hist_alpha)
            hist_beta_json = json.dumps(hist_beta)
            hist_gamma_json = json.dumps(hist_gamma)
            current_pct_json = json.dumps(
                [current_pct['Delta'], current_pct['Theta'], current_pct['Alpha'], current_pct['Beta'],
                 current_pct['Gamma']])
            avg_pct_json = json.dumps([avg_delta, avg_theta, avg_alpha, avg_beta, avg_gamma])

            chart_script = f"""
                
                    // 睡眠评分趋势图
                    var scoreChart = echarts.init(document.getElementById('scoreTrendChart'));
                    scoreChart.setOption({{
                        title: {{ text: '睡眠评分历史趋势', left: 'center', textStyle: {{ color: '#ffd966' }} }},
                        tooltip: {{ trigger: 'axis' }},
                        xAxis: {{ type: 'category', data: {hist_labels_json}, name: '测试时间', axisLabel: {{ rotate: 30, color: '#eef4ff' }} }},
                        yAxis: {{ type: 'value', name: '睡眠评分', min: 0, max: 100, axisLabel: {{ color: '#eef4ff' }} }},
                        series: [{{
                            name: '睡眠评分',
                            type: 'line',
                            data: {hist_scores_json},
                            smooth: true,
                            lineStyle: {{ color: '#ffd966', width: 3 }},
                            symbol: 'circle',
                            symbolSize: 8,
                            itemStyle: {{ color: '#ffaa33' }},
                            markPoint: {{
                                data: [
                                    {{ type: 'max', name: '最高分' }},
                                    {{ type: 'min', name: '最低分' }}
                                ]
                            }}
                        }}],
                        backgroundColor: 'transparent',
                        grid: {{ borderWidth: 0, containLabel: true }},
                        textStyle: {{ color: '#eef4ff' }}
                    }});

                    // 阶段对比柱状图（当前 vs 历史平均）
                    var stageChart = echarts.init(document.getElementById('stageCompareChart'));
                    stageChart.setOption({{
                        title: {{ text: '睡眠阶段分布对比', left: 'center', textStyle: {{ color: '#ffd966' }} }},
                        tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
                        legend: {{ data: ['当前', '历史平均'], textStyle: {{ color: '#eef4ff' }}, top: 30 }},
                        xAxis: {{ type: 'category', data: ['深睡期(Delta)', '浅睡期(Theta)', 'REM期(Alpha)', '清醒期(Beta)', '活跃期(Gamma)'], axisLabel: {{ rotate: 20, color: '#eef4ff' }} }},
                        yAxis: {{ type: 'value', name: '百分比 (%)', axisLabel: {{ color: '#eef4ff' }} }},
                        series: [
                            {{ name: '当前', type: 'bar', data: {current_pct_json}, itemStyle: {{ color: '#5fa3dd' }} }},
                            {{ name: '历史平均', type: 'bar', data: {avg_pct_json}, itemStyle: {{ color: '#b3d4ff' }} }}
                        ],
                        backgroundColor: 'transparent',
                        grid: {{ borderWidth: 0, containLabel: true }},
                        textStyle: {{ color: '#eef4ff' }}
                    }});
                
                """
        else:
            # 没有历史记录时的占位内容
            compare_html = """
                <div class="section_compant">
                    <h2 class='biaoti'>📈 历史对比分析</h2>
                    <p>暂无历史记录，无法进行对比分析。请完成多次测试后再来查看改善趋势。</p>
                </div>
                """
            chart_script = ""

        # 原有的饼图 script 保持不变，但需要在饼图之后添加对比图
        # 原有饼图 script 变量名为 pie_script（可能需要调整）
        # 我们直接在返回的HTML中，在饼图部分后面添加上面的 compare_html 和 chart_script

        # 构建完整 HTML（原有代码保留，仅插入 compare_html 和 chart_script）
        report_html = f"""
            <!DOCTYPE html>
            <html>
                <head>
                    <meta charset="UTF-8">
                    <title>睡眠分析报告 {datetime.now().strftime('%Y%m%d_%H%M%S')}</title>
                    <style>
                        /* 全局重置与基础色调 */
                        * {{
                            margin: 0;
                            padding: 0;
                            box-sizing: border-box;
                        }}
                        body.body_report {{
                            background: linear-gradient(135deg, #0a2f6c 0%, #144a7c 100%);
                            font-family: 'Segoe UI', 'Roboto', 'Microsoft YaHei', sans-serif;
                            margin: 0;
                            padding: 30px 20px;
                            line-height: 1.6;
                            color: #eef4ff;
                        }}
                        /* 主容器 - 增加最大宽度和居中 */
                        .report-container {{
                            max-width: 1400px;
                            margin: 0 auto;
                        }}
                        /* 头部区域 */
                        .header_compant {{
                            background: linear-gradient(135deg, rgba(30,90,156,0.9) 0%, rgba(44,123,192,0.9) 100%);
                            backdrop-filter: blur(4px);
                            padding: 30px;
                            border-radius: 28px;
                            text-align: center;
                            margin-bottom: 30px;
                            box-shadow: 0 12px 25px rgba(0,0,0,0.3);
                            border: 1px solid rgba(255,255,255,0.2);
                        }}
                        .header_compant h1 {{
                            font-size: 2rem;
                            margin-bottom: 10px;
                            letter-spacing: 1px;
                        }}
                        .header_compant p {{
                            font-size: 0.9rem;
                            opacity: 0.9;
                        }}
                        /* 通用卡片样式 */
                        .section_compant {{
                            background: rgba(20, 40, 70, 0.75);
                            backdrop-filter: blur(4px);
                            padding: 25px;
                            margin: 25px 0;
                            border-radius: 24px;
                            box-shadow: 0 8px 20px rgba(0,0,0,0.2);
                            border: 1px solid rgba(255,255,255,0.2);
                            transition: transform 0.2s ease, box-shadow 0.2s ease;
                        }}
                        .section_compant:hover {{
                            transform: translateY(-2px);
                            box-shadow: 0 12px 25px rgba(0,0,0,0.3);
                        }}
                        /* 标题样式统一 */
                        .biaoti {{
                            color: #ffd966;
                            border-left: 5px solid #ffaa33;
                            padding-left: 18px;
                            margin-top: 0;
                            margin-bottom: 20px;
                            font-size: 1.6rem;
                            font-weight: 600;
                        }}
                        h3, h4 {{
                            color: #ffd966;
                            margin: 0 0 15px 0;
                        }}
                        /* 表格样式 - 更现代、响应式 */
                        .stats-table_compant {{
                            width: 100%;
                            border-collapse: collapse;
                            margin: 20px 0;
                            font-size: 0.9rem;
                            border-radius: 16px;
                            overflow: hidden;
                            background: rgba(255,255,255,0.05);
                            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                        }}
                        .stats-table_compant th,
                        .stats-table_compant td {{
                            padding: 12px 15px;
                            text-align: left;
                            border-bottom: 1px solid rgba(255,255,255,0.15);
                            border-right: 1px solid rgba(255,255,255,0.1);
                        }}
                        .stats-table_compant th:last-child,
                        .stats-table_compant td:last-child {{
                            border-right: none;
                        }}
                        .stats-table_compant th {{
                            background: rgba(30, 90, 156, 0.9);
                            color: white;
                            font-weight: 600;
                            font-size: 0.9rem;
                            text-transform: uppercase;
                            letter-spacing: 0.5px;
                        }}
                        .stats-table_compant tr:hover {{
                            background: rgba(255,255,255,0.1);
                        }}
                        .stats-table_compant tbody tr:nth-child(even) {{
                            background: rgba(255,255,255,0.03);
                        }}
                        /* 睡眠分析列表优化 */
                        .sleep-analysis ul {{
                            list-style: none;
                            padding: 0;
                            margin: 20px 0;
                            display: flex;
                            flex-wrap: wrap;
                            gap: 12px;
                        }}
                        .sleep-analysis li {{
                            background: rgba(255,255,255,0.15);
                            padding: 8px 18px;
                            border-radius: 40px;
                            font-size: 0.9rem;
                            backdrop-filter: blur(4px);
                            transition: background 0.2s;
                        }}
                        .sleep-analysis li:hover {{
                            background: rgba(255,255,255,0.25);
                        }}
                        .sleep-score {{
                            text-align: center;
                            margin-top: 25px;
                            font-size: 1.2rem;
                            font-weight: bold;
                            background: rgba(0,0,0,0.2);
                            padding: 15px;
                            border-radius: 40px;
                        }}
                        /* 图表容器美化 */
                        .chart-container {{
                            background: rgba(0,0,0,0.2);
                            border-radius: 20px;
                            padding: 15px;
                            margin: 20px 0;
                        }}
                        /* 对比分析特殊样式 */
                        .compare-badge {{
                            display: inline-block;
                            background: #ffaa33;
                            color: #0a2f6c;
                            padding: 4px 12px;
                            border-radius: 20px;
                            font-size: 0.8rem;
                            font-weight: bold;
                            margin-left: 12px;
                        }}
                        /* AI评估内容样式 */
                        .ai-content {{
                            background: rgba(0,0,0,0.2);
                            padding: 20px;
                            border-radius: 20px;
                            margin-top: 10px;
                        }}
                        .ai-content p {{
                            margin: 10px 0;
                        }}
                        .ai-content strong {{
                            color: #ffd966;
                        }}
                        /* 响应式设计 */
                        @media (max-width: 768px) {{
                            body.body_report {{
                                padding: 15px;
                            }}
                            .header_compant h1 {{
                                font-size: 1.4rem;
                            }}
                            .section_compant {{
                                padding: 18px;
                            }}
                            .stats-table_compant th,
                            .stats-table_compant td {{
                                padding: 8px 10px;
                                font-size: 0.75rem;
                            }}
                            .sleep-analysis li {{
                                font-size: 0.75rem;
                                padding: 5px 12px;
                            }}
                            .biaoti {{
                                font-size: 1.3rem;
                            }}
                            .chart-container {{
                                padding: 8px;
                            }}
                        }}
                        /* 打印样式 */
                        @media print {{
                            body.body_report {{
                                background: white;
                                color: black;
                                padding: 0;
                            }}
                            .section_compant {{
                                background: white;
                                border: 1px solid #ccc;
                                box-shadow: none;
                                color: black;
                            }}
                            .header_compant {{
                                background: #f0f0f0;
                                color: black;
                            }}
                            .stats-table_compant th {{
                                background: #ccc;
                                color: black;
                            }}
                            .biaoti {{
                                color: #0a2f6c;
                            }}
                            .chart-container {{
                                break-inside: avoid;
                            }}
                            .stats-table_compant tr:hover {{
                                background: none;
                            }}
                        }}
                    </style>
                    <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
                </head>
                <body class="body_report">
                    <div class="report-container">
                        <!-- 头部 -->
                        <div class="header_compant">
                            <h1 class="biaoti">🧠 睡眠脑电分析报告</h1>
                            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 文件: {os.path.basename(self.file_path)}</p>
                        </div>
                
                        <div class="section_compant">{stats}</div>
                
                        <div class="section_compant">
                            {sleep_analysis}
                             <div id="sleepPieChart" style="width: 100%; height: 400px; min-height: 400px;"></div>
                        </div>
                
                        {compare_html}   <!-- 对比分析部分已包含内部样式和图表容器 -->
                
                        <div class="section_compant">
                            <h2 class='biaoti'>🤖 AI智能评估</h2>
                            <div class="ai-content">
                                {cleaned_ai_content}
                            </div>
                        </div>
                    </div>
                    <script>
                        // 原有饼图代码
                        var pieChart = echarts.init(document.getElementById('sleepPieChart'));
                        pieChart.setOption({{
                            color: ['#1e5a9c', '#2c7bc0', '#5fa3dd', '#8bc1f0', '#b3d4ff'],
                            title: {{ text: '睡眠阶段分布', left: 'center', textStyle: {{ fontSize: 16, fontWeight: 'bold', color: '#ffd966' }} }},
                            tooltip: {{ trigger: 'item', formatter: '{{a}} <br/>{{b}}: {{c}}%' }},
                            legend: {{ orient: 'vertical', left: 'left', textStyle: {{ color: '#eef4ff' }}, data: ['深睡期 (Delta)', '浅睡期 (Theta)', 'REM期 (Alpha)', '清醒期 (Beta)', '活跃期 (Gamma)'] }},
                            series: [{{
                                name: '睡眠阶段',
                                type: 'pie',
                                radius: '55%',
                                center: ['60%', '50%'],
                                data: [
                                    {{ value: {current_pct['Delta']:.1f}, name: '深睡期 (Delta)' }},
                                    {{ value: {current_pct['Theta']:.1f}, name: '浅睡期 (Theta)' }},
                                    {{ value: {current_pct['Alpha']:.1f}, name: 'REM期 (Alpha)' }},
                                    {{ value: {current_pct['Beta']:.1f}, name: '清醒期 (Beta)' }},
                                    {{ value: {current_pct['Gamma']:.1f}, name: '活跃期 (Gamma)' }}
                                ],
                                label: {{ show: true, formatter: '{{b}}: {{d}}%', color: '#eef4ff' }},
                            }}]
                        }});
                        {chart_script}   <!-- 对比图脚本 -->
                    </script>
                </body>
            </html>
            """
        return report_html

    def call_volcengine_api(self, api_key, prompt, model="doubao-seed-1-6-lite-251015"):
        """
        调用火山引擎AI API进行对话补全
        
        Args:
            api_key (str): 火山引擎API密钥，用于身份验证
            prompt (str): 发送给AI的提示词内容
            model (str, optional): 指定使用的AI模型，默认为"doubao-seed-1-6-lite-251015"
            
        Returns:
            str: API返回的响应内容，如果调用失败则返回错误信息HTML字符串
        """
        try:
            if not api_key or api_key == "your_api_key_here":
                return "<div class='error'><h3>⚠️ API密钥未配置</h3><p>请配置有效的火山引擎API密钥</p></div>"
            
            # 记录prompt大小
            prompt_size = len(prompt.encode('utf-8'))
            logger.info(f"Calling VolcEngine API with prompt size: {prompt_size} bytes")
            
            client = Ark(api_key=api_key)
            messages = [{"role": "user", "content": prompt}]
            # 设置更合理的超时和重试参数
            response = client.chat.completions.create( 
                model=model,
                messages=messages,
                temperature=0.3,
                timeout=100,  # 进一步减少超时时间
                 
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = f"<div class='error'><h3>❌ AI调用失败</h3><p>{str(e)}</p></div>"
            logger.error(f"VolcEngine API调用失败: {str(e)}")
            # 提供默认的AI响应以防API调用失败
            default_response = "<p><strong>睡眠质量评估：</strong>根据数据分析，您的睡眠质量处于<strong style='color:#faad14'>一般水平</strong>。</p><p><strong>阶段分析：</strong>深睡期占比适中，浅睡期较为稳定，REM期表现正常。</p><p><strong>健康建议：</strong><span style='color:red'>建议保持规律作息，避免睡前使用电子设备，创造良好的睡眠环境。</span></p>"
            return default_response

# 测试函数（修复语法错误）
if __name__ == "__main__":
    test_file = "test_data.csv"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("时间,Delta,Theta,Alpha,Beta,Gamma\n2024-01-01 10:00:00,25,30,20,15,10\n")
    
    analyzer = EEGAnalyzer(test_file, "test_api_key")
    result = analyzer.analyze()
    print("分析结果:", result)  # 修复中文括号问题