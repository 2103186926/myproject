#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
集成测试脚本
自动生成测试用例、运行训练、生成评估报告
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# 注释掉调试器代码，生产环境不需要
import debugpy
try:
    debugpy.listen(("localhost", 9501))
    print("Waiting for debugger attach")
    debugpy.wait_for_client()
except Exception as e:
    pass

def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"▶ {description}")
    print(f"  命令: {cmd}\n")
    
    start_time = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
    elapsed = time.time() - start_time
    
    if result.returncode == 0:
        print(f"✅ 成功 (耗时: {elapsed:.2f}秒)\n")
        return True
    else:
        print(f"❌ 失败 (退出码: {result.returncode})\n")
        return False


def check_dependencies():
    """检查依赖是否安装"""
    print_section("检查依赖")
    
    required_packages = [
        'torch',
        'torch_geometric',
        'networkx',
        'numpy',
        'pandas',
        'matplotlib',
        'seaborn',
        'sklearn',
        'transformers',
        'tqdm'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (未安装)")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  缺少以下依赖包: {', '.join(missing)}")
        print("请运行: pip install " + " ".join(missing))
        return False
    
    print("\n✅ 所有依赖已安装")
    return True


def generate_test_cases():
    """生成测试用例"""
    print_section("生成测试用例")
    
    cmd = "python test_case_generator.py"
    return run_command(cmd, "生成海洋科学场景测试用例")


def generate_config():
    """生成配置文件"""
    print_section("生成配置文件")
    
    cmd = 'python -c "from config import save_default_config; save_default_config(\'./test_config.json\')"'
    return run_command(cmd, "生成默认配置文件")


def run_training(quick_mode=False):
    """运行训练"""
    print_section("运行模型训练")
    
    # 检查测试用例是否存在
    if not os.path.exists('./test_cases/labels.csv'):
        print("❌ 测试用例不存在，请先生成测试用例")
        return False
    
    # 构建训练命令
    cmd = [
        "python main_workflow_v2.py",
        "--source_dir ./test_cases",
        "--label_file ./test_cases/labels.csv",
        "--output_dir ./test_output",
        "--log_file ./test_output/training.log"
    ]
    
    if quick_mode:
        print("⚡ 快速模式：使用较少的训练轮数")
        # 可以通过修改配置文件来实现快速训练
    
    cmd_str = " ".join(cmd)
    return run_command(cmd_str, "训练CFG-GNN和FCG-GNN模型")


def generate_framework_diagram():
    """生成框架图"""
    print_section("生成框架图")
    
    cmd = "python generate_dynamic_framework_diagram.py"
    return run_command(cmd, "生成动态GNN框架图")


def check_results():
    """检查结果文件"""
    print_section("检查输出结果")
    
    output_dir = Path("./test_output")
    
    expected_files = [
        "cfg_gnn_model.pth",
        "fcg_gnn_model.pth",
        "training_history.json",
        "config.json",
        "training.log",
        "confusion_matrix.png",
        "roc_curve.png",
        "evaluation_results.json"
    ]
    
    all_exist = True
    for file in expected_files:
        file_path = output_dir / file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✅ {file} ({size:,} bytes)")
        else:
            print(f"❌ {file} (不存在)")
            all_exist = False
    
    return all_exist


def print_summary(results):
    """打印测试总结"""
    print_section("测试总结")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed
    
    print(f"总测试项: {total}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print()
    
    for step, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {step}: {status}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！")
        return True
    else:
        print(f"\n⚠️  有 {failed} 项测试失败")
        return False


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("  Python容器逃逸代码检测系统 - 集成测试")
    print("=" * 70)
    
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description="集成测试脚本")
    parser.add_argument("--quick", action="store_true", help="快速模式（减少训练轮数）")  #! 勾选后才为True
    parser.add_argument("--skip-deps", action="store_true", help="跳过依赖检查")
    parser.add_argument("--skip-train", action="store_true", help="跳过训练步骤")
    parser.add_argument("--only-generate", action="store_true", help="仅生成测试用例")
    args = parser.parse_args()
    
    results = {}
    
    # 1. 检查依赖
    if not args.skip_deps:  # not F
        results["依赖检查"] = check_dependencies()
        if not results["依赖检查"]:
            print("\n❌ 依赖检查失败，请安装缺失的依赖包")
            return 1
    
    # 2. 生成测试用例
    results["生成测试用例"] = generate_test_cases()
    if not results["生成测试用例"]:
        print("\n❌ 测试用例生成失败")
        return 1
    
    if args.only_generate:
        print("\n✅ 测试用例生成完成")
        return 0
    
    # 3. 生成配置文件
    results["生成配置"] = generate_config()
    
    # 4. 运行训练
    if not args.skip_train:
        results["模型训练"] = run_training(quick_mode=args.quick)
        
        # 5. 检查结果
        if results["模型训练"]:
            results["结果检查"] = check_results()
    
    # 6. 生成框架图
    results["生成框架图"] = generate_framework_diagram()
    
    # 打印总结
    success = print_summary(results)
    
    if success:
        print("\n" + "=" * 70)
        print("  测试完成！查看结果:")
        print("  - 训练日志: ./test_output/training.log")
        print("  - 模型文件: ./test_output/*.pth")
        print("  - 评估结果: ./test_output/evaluation_results.json")
        print("  - 可视化图: ./test_output/*.png")
        print("=" * 70 + "\n")
        return 0
    else:
        print("\n" + "=" * 70)
        print("  测试失败，请检查错误信息")
        print("=" * 70 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
