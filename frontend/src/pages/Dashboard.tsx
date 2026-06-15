import React, { useEffect } from 'react';
import * as echarts from 'echarts/core';
import { BarChart } from 'echarts/charts';
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

// 仅注册当前页面实际使用的 ECharts 模块，缩小构建体积。
echarts.use([BarChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer]);

const Dashboard: React.FC = () => {
  // 初始化图表
  useEffect(() => {
    const chartDom = document.getElementById('main-chart');
    if (chartDom) {
      const myChart = echarts.init(chartDom);
      const option = {
        animation: false,
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        legend: {
          data: ['视频上传', '视频下载', '视频解析', '用户访问', '系统处理']
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'value'
        },
        yAxis: {
          type: 'category',
          data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        },
        series: [
          {
            name: '视频上传',
            type: 'bar',
            stack: 'total',
            label: {
              show: true
            },
            emphasis: {
              focus: 'series'
            },
            data: [120, 132, 101, 134, 90, 230, 210]
          },
          {
            name: '视频下载',
            type: 'bar',
            stack: 'total',
            label: {
              show: true
            },
            emphasis: {
              focus: 'series'
            },
            data: [220, 182, 191, 234, 290, 330, 310]
          },
          {
            name: '视频解析',
            type: 'bar',
            stack: 'total',
            label: {
              show: true
            },
            emphasis: {
              focus: 'series'
            },
            data: [150, 232, 201, 154, 190, 330, 410]
          },
          {
            name: '用户访问',
            type: 'bar',
            stack: 'total',
            label: {
              show: true
            },
            emphasis: {
              focus: 'series'
            },
            data: [320, 332, 301, 334, 390, 330, 320]
          },
          {
            name: '系统处理',
            type: 'bar',
            stack: 'total',
            label: {
              show: true
            },
            emphasis: {
              focus: 'series'
            },
            data: [820, 932, 901, 934, 1290, 1330, 1320]
          }
        ]
      };
      myChart.setOption(option);
      
      return () => {
        myChart.dispose();
      };
    }
  }, []);

  return (
    <div className="space-y-6">
      {/* 欢迎卡片 */}
      <div className="bg-white shadow-sm rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-800">欢迎回来，管理员</h2>
          <div className="flex space-x-2">
            <button className="btn-primary">
              新建任务
            </button>
            <button className="btn-secondary">
              导入数据
            </button>
          </div>
        </div>
        <p className="text-gray-600 mb-4">
          您有 3 个待处理的任务，5 个新消息，2 个数据更新通知。
        </p>
        <div className="grid grid-cols-4 gap-4">
          {[
            { title: '总视频数', value: '1,248', change: '+12%', icon: 'fa-video' },
            { title: '活跃用户', value: '8,742', change: '+5%', icon: 'fa-user-check' },
            { title: '处理成功率', value: '98.2%', change: '+0.5%', icon: 'fa-percentage' },
            { title: '存储使用', value: '245GB', change: '+18%', icon: 'fa-hdd' }
          ].map((item) => (
            <div
              key={item.title}
              className="bg-gray-50 p-4 rounded-lg border border-gray-200"
            >
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm text-gray-500">{item.title}</p>
                  <p className="text-2xl font-semibold text-gray-800 mt-1">{item.value}</p>
                </div>
                <span
                  className={`text-xs px-2 py-1 rounded-full ${
                    item.change.startsWith('+')
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {item.change}
                </span>
              </div>
              <div className="mt-4 flex items-center">
                <i className={`fas ${item.icon} text-blue-500 mr-2`}></i>
                <span className="text-xs text-gray-500">查看详情</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 主图表 */}
      <div className="bg-white shadow-sm rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-800">系统使用分析</h2>
          <div className="flex space-x-2">
            <button className="px-3 py-1 bg-white border border-gray-300 text-gray-700 text-sm rounded-button hover:bg-gray-50">
              日
            </button>
            <button className="px-3 py-1 bg-white border border-gray-300 text-gray-700 text-sm rounded-button hover:bg-gray-50">
              周
            </button>
            <button className="px-3 py-1 bg-blue-600 text-white text-sm rounded-button hover:bg-blue-700">
              月
            </button>
            <button className="px-3 py-1 bg-white border border-gray-300 text-gray-700 text-sm rounded-button hover:bg-gray-50">
              年
            </button>
          </div>
        </div>
        <div id="main-chart" className="w-full h-80"></div>
      </div>

      {/* 最近活动和项目进度 */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white shadow-sm rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">最近活动</h2>
          <div className="space-y-4">
            {[
              {
                user: '张三',
                action: '上传了新视频',
                time: '10分钟前',
                avatar: 'male'
              },
              {
                user: '李四',
                action: '完成了视频解析',
                time: '25分钟前',
                avatar: 'female'
              },
              {
                user: '王五',
                action: '下载了视频文件',
                time: '1小时前',
                avatar: 'male'
              },
              {
                user: '赵六',
                action: '更新了系统配置',
                time: '2小时前',
                avatar: 'female'
              },
              {
                user: '钱七',
                action: '创建了新任务',
                time: '3小时前',
                avatar: 'male'
              }
            ].map((item, index) => (
              <div key={index} className="flex items-start">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center mr-3">
                  <i className="fas fa-user text-white text-sm"></i>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-800">
                    {item.user} <span className="font-normal text-gray-600">{item.action}</span>
                  </p>
                  <p className="text-xs text-gray-500 mt-1">{item.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 系统状态 */}
        <div className="bg-white shadow-sm rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">系统状态</h2>
          <div className="space-y-4">
            {[
              {
                name: 'CPU使用率',
                progress: 65,
                status: 'normal',
                value: '65%'
              },
              {
                name: '内存使用率',
                progress: 45,
                status: 'normal',
                value: '45%'
              },
              {
                name: '磁盘使用率',
                progress: 80,
                status: 'warning',
                value: '80%'
              },
              {
                name: '网络带宽',
                progress: 30,
                status: 'normal',
                value: '30%'
              }
            ].map((item, index) => (
              <div key={index}>
                <div className="flex justify-between items-center mb-1">
                  <h3 className="text-sm font-medium text-gray-800">{item.name}</h3>
                  <span className="text-xs text-gray-500">
                    {item.value}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      item.status === 'warning' ? 'bg-yellow-500' : 'bg-blue-600'
                    }`}
                    style={{ width: `${item.progress}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
