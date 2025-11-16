
# 启动前端服务（后台运行）
echo "正在启动前端服务..."
cd front_end

# 检查 node_modules 是否存在
if [ ! -d "node_modules" ]; then
    echo "检测到未安装前端依赖，正在安装..."
    npm install
fi

npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# 等待前端启动
sleep 3

# 检查前端是否成功启动
if ps -p $FRONTEND_PID > /dev/null; then
    echo "✓ 前端服务已启动 (PID: $FRONTEND_PID)"
    echo "  前端日志: frontend.log"
    echo "前端地址: http://localhost:5173"
else
    echo "✗ 前端服务启动失败，请查看 frontend.log"
    exit 1
fi


#####

# 启动后端服务（后台运行）
cd back_end
python backend.py 
BACKEND_PID=$!
cd ..



# echo "=========================================="
# echo "服务启动完成！"
# echo "=========================================="
# echo "前端地址: http://localhost:5173"
# echo "后端API: http://localhost:5000"
echo ""
echo "按 Ctrl+C 停止服务"
echo "或者运行以下命令停止:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo "=========================================="

# 等待用户中断
wait