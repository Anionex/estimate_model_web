import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import ApiUtill from "../ApiUtill";
import '../App.css';
import {
  Card,
  CardHeader,
  CardBody,
  Button,
  Textarea,
  Select,
  SelectItem
} from "@nextui-org/react";
import { CircularProgress } from "@nextui-org/react";

function DevAdminPage() {
  const [query, setQuery] = useState("");
  const [selectedModel, setSelectedModel] = useState("gpt");
  const [output, setOutput] = useState([]);
  const [outputText, setOutputText] = useState(""); // 累积的原始输出文本
  const [isRunning, setIsRunning] = useState(false);
  const outputEndRef = useRef(null);
  const eventSourceRef = useRef(null);

  // 自动滚动到底部
  const scrollToBottom = () => {
    outputEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [outputText, output]);

  // 清理函数
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  // 添加输出消息
  const addOutputMessage = (type, message, timestamp, traceback = null) => {
    // 累积原始输出文本，保持原始格式（包括换行符）
    setOutputText(prev => prev + message);
    
    // 同时保存结构化数据用于错误堆栈显示
    if (traceback || type === 'error') {
      setOutput(prev => [...prev, { type, message, timestamp, traceback }]);
    }
  };

  // 获取消息颜色样式
  const getMessageStyle = (type) => {
    switch (type) {
      case 'error':
        return 'text-red-400';
      case 'warning':
        return 'text-yellow-400';
      case 'info':
        return 'text-blue-400';
      case 'done':
        return 'text-green-400';
      case 'stdout':
      default:
        return 'text-gray-300';
    }
  };

  // 开始调试
  const handleStartDebug = async () => {
    if (!query.trim()) {
      alert("请输入问题");
      return;
    }

    if (isRunning) {
      alert("调试正在进行中，请等待完成");
      return;
    }

    // 清空之前的输出
    setOutput([]);
    setOutputText("");
    setIsRunning(true);

    try {
      // 使用 fetch 来处理 SSE 流
      const response = await fetch(ApiUtill.url_root + 'dev_admin/debug_model', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query.trim(),
          model: selectedModel
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // 保留最后一个不完整的行

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              addOutputMessage(
                data.type,
                data.message,
                data.timestamp,
                data.traceback
              );
            } catch (e) {
              console.error('解析SSE数据失败:', e, line);
            }
          }
        }
      }

      // 处理剩余的buffer
      if (buffer.startsWith('data: ')) {
        try {
          const data = JSON.parse(buffer.slice(6));
          addOutputMessage(
            data.type,
            data.message,
            data.timestamp,
            data.traceback
          );
        } catch (e) {
          console.error('解析SSE数据失败:', e);
        }
      }

    } catch (error) {
      console.error('调试错误:', error);
      addOutputMessage(
        'error',
        `连接错误: ${error.message}`,
        new Date().toISOString()
      );
    } finally {
      setIsRunning(false);
    }
  };

  // 清空输出
  const handleClear = () => {
    setOutput([]);
    setOutputText("");
  };

  return (
    <div className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-2 min-h-screen">
      <div className="w-full mx-auto">
        <Card className="bg-gray-800/50 backdrop-blur-sm border border-gray-700">
          <CardHeader className="flex flex-col gap-2">
            <h1 className="text-3xl font-bold text-white">模型调试面板</h1>
            <p className="text-gray-400">实时调试和监控模型输出</p>
          </CardHeader>
          <CardBody className="gap-4">
            {/* 输入区域 */}
            <div className="flex flex-col gap-4">
              <Textarea
                label="输入问题"
                placeholder="请输入要调试的问题..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                minRows={3}
                className="w-full"
                classNames={{
                  input: "text-white",
                  label: "text-gray-300"
                }}
              />

              <div className="flex gap-4 items-end">
                <Select
                  label="选择模型"
                  selectedKeys={[selectedModel]}
                  onSelectionChange={(keys) => {
                    const selected = Array.from(keys)[0];
                    setSelectedModel(selected);
                  }}
                  className="flex-1"
                  classNames={{
                    trigger: "bg-gray-700 border-gray-600",
                    label: "text-gray-300"
                  }}
                >
                  <SelectItem key="gpt" value="gpt">GPT Model</SelectItem>
                  <SelectItem key="ourmodel" value="ourmodel">Our Model</SelectItem>
                  <SelectItem key="xxmodel" value="xxmodel">XX Model (TripAdvisor)</SelectItem>
                </Select>

                <Button
                  color="primary"
                  onClick={handleStartDebug}
                  disabled={isRunning || !query.trim()}
                  className="min-w-32"
                >
                  {isRunning ? (
                    <div className="flex items-center gap-2">
                      <CircularProgress size="sm" color="white" />
                      <span>运行中...</span>
                    </div>
                  ) : (
                    "开始调试"
                  )}
                </Button>

                <Button
                  color="default"
                  variant="bordered"
                  onClick={handleClear}
                  disabled={isRunning}
                >
                  清空输出
                </Button>
              </div>
            </div>

            {/* 输出显示区域 */}
            <div className="mt-4">
              <div className="text-sm text-gray-400 mb-2">实时输出：</div>
              <div className="bg-black rounded-lg p-4 h-128 overflow-y-auto font-mono text-sm">
                {outputText === "" ? (
                  <div className="text-gray-500 italic">等待输出...</div>
                ) : (
                  <pre className="whitespace-pre-wrap text-gray-300 m-0">
                    {outputText}
                  </pre>
                )}
                {/* 显示错误堆栈（如果有） */}
                {output.filter(item => item.traceback).map((item, index) => (
                  <div key={`error-${index}`} className="mt-2">
                    <div className="text-red-400 font-bold">错误堆栈：</div>
                    <div className="ml-4 mt-1 text-red-300 text-xs whitespace-pre-wrap">
                      {item.traceback}
                    </div>
                  </div>
                ))}
                <div ref={outputEndRef} />
              </div>
            </div>

            {/* 状态说明 */}
            <div className="mt-4 flex gap-4 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-400"></div>
                <span className="text-gray-400">错误</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
                <span className="text-gray-400">警告</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-blue-400"></div>
                <span className="text-gray-400">信息</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-green-400"></div>
                <span className="text-gray-400">完成</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-gray-300"></div>
                <span className="text-gray-400">标准输出</span>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

export default DevAdminPage;

