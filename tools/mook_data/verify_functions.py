#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""验证新增函数是否正确添加"""

import sys
sys.path.insert(0, 'tools')

from mock_data import OceanScenarioLibrary

lib = OceanScenarioLibrary()

print("="*60)
print("函数模板验证报告")
print("="*60)
print()

print(f"场景数量: {len(lib.SCENARIOS)}")
print(f"函数名称数量: {len(lib.FUNCTION_NAMES)}")
print(f"函数模板数量: {len(lib.FUNCTION_TEMPLATES)}")
print()

# 验证新增函数
new_functions = [
    # Part 1: 数据加载与预处理
    'load_netcdf_data', 'load_hdf5_data', 'load_geotiff_data', 'parse_observation_data',
    'preprocess_satellite_data', 'fill_missing_values', 'normalize_data', 'standardize_coordinates',
    # Part 2: 时空处理
    'interpolate_spatial_data', 'interpolate_temporal_data', 'resample_timeseries', 'grid_irregular_data',
    'apply_spatial_filter', 'apply_temporal_filter', 'calculate_spatial_gradient', 'calculate_temporal_gradient',
    'detect_spatial_anomalies', 'detect_temporal_anomalies', 'extract_spatial_features', 'extract_temporal_features',
    # Part 3: 海洋要素计算
    'calculate_temperature_field', 'calculate_salinity_field', 'calculate_density_field', 'calculate_current_velocity',
    'calculate_wave_height', 'calculate_mixed_layer_depth', 'calculate_thermocline_depth', 'calculate_upwelling_index',
    'calculate_ekman_transport', 'calculate_geostrophic_current', 'calculate_vorticity', 'calculate_divergence',
    'calculate_stratification', 'calculate_buoyancy_frequency', 'calculate_richardson_number',
    # Part 4: 模式模拟与预测
    'run_ocean_model', 'initialize_model_state', 'update_boundary_conditions', 'assimilate_observation_data',
    'forecast_ocean_state', 'predict_temperature', 'predict_salinity', 'predict_current',
    'simulate_wave_propagation', 'simulate_pollutant_dispersion',
    # Part 5: 特征识别与分析
    'detect_ocean_fronts', 'identify_eddies', 'track_eddy_trajectory', 'detect_upwelling',
    'identify_water_masses', 'classify_ocean_regimes', 'segment_ocean_regions', 'detect_bloom_events',
    'identify_fishing_grounds', 'locate_thermal_anomalies', 'find_convergence_zones', 'detect_internal_waves',
    # Part 6: 统计分析与评估
    'compute_climatology', 'calculate_anomaly', 'perform_eof_analysis', 'compute_correlation',
    'calculate_trend', 'assess_model_performance', 'validate_forecast', 'estimate_uncertainty',
    'quantify_variability',
    # Part 7: 可视化与输出
    'visualize_spatial_field', 'plot_time_series', 'generate_contour_map', 'create_vector_plot',
    'export_netcdf', 'export_geotiff', 'generate_statistics_report', 'create_interactive_map',
]

print(f"验证 {len(new_functions)} 个新增函数:")
print()

found = 0
missing = []

for func in new_functions:
    if func in lib.FUNCTION_TEMPLATES:
        found += 1
        print(f"  ✓ {func}")
    else:
        missing.append(func)
        print(f"  ✗ {func} 未找到")

print()
print("="*60)
print(f"验证结果: {found}/{len(new_functions)} 个函数已添加")

if missing:
    print(f"缺失函数: {missing}")
else:
    print("✓ 所有新增函数都已正确添加！")

print("="*60)
