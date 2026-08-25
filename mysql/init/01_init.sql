-- ============================================================
-- 毛仔天气 - 数据库初始化脚本
-- 数据库: maozi_weather
-- 字符集: utf8mb4
-- ============================================================

USE maozi_weather;

-- ============================================================
-- 1. 用户表
-- ============================================================
CREATE TABLE IF NOT EXISTS `users` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    `username` VARCHAR(50) NOT NULL COMMENT '用户名',
    `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希(bcrypt)',
    `real_name` VARCHAR(50) DEFAULT NULL COMMENT '真实姓名',
    `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
    `is_admin` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否管理员',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`),
    KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================================
-- 2. 城市/站点库
-- ============================================================
CREATE TABLE IF NOT EXISTS `cities` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '城市ID',
    `city_name` VARCHAR(100) NOT NULL COMMENT '城市名称',
    `city_code` VARCHAR(20) DEFAULT NULL COMMENT '行政区划代码',
    `station_id` VARCHAR(20) DEFAULT NULL COMMENT '气象站点ID',
    `province` VARCHAR(50) DEFAULT NULL COMMENT '所属省份',
    `longitude` DECIMAL(10, 6) DEFAULT NULL COMMENT '经度',
    `latitude` DECIMAL(10, 6) DEFAULT NULL COMMENT '纬度',
    `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_city_name` (`city_name`),
    KEY `idx_city_code` (`city_code`),
    KEY `idx_station_id` (`station_id`),
    KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='城市站点库';

-- ============================================================
-- 3. 用户关注城市
-- ============================================================
CREATE TABLE IF NOT EXISTS `user_cities` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `city_id` BIGINT NOT NULL COMMENT '城市ID',
    `sort_order` INT NOT NULL DEFAULT 0 COMMENT '排序',
    `view_mode` VARCHAR(10) NOT NULL DEFAULT 'city' COMMENT '查看模式: city-城市, station-站点',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_city_id` (`city_id`),
    UNIQUE KEY `uk_user_city` (`user_id`, `city_id`),
    CONSTRAINT `fk_user_cities_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_user_cities_city` FOREIGN KEY (`city_id`) REFERENCES `cities` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户关注城市';

-- ============================================================
-- 4. 实况天气（缓存最新数据）
-- ============================================================
CREATE TABLE IF NOT EXISTS `weather_realtime` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'ID',
    `city_id` BIGINT NOT NULL COMMENT '城市ID',
    `station_id` VARCHAR(20) DEFAULT NULL COMMENT '站点ID',
    `temperature` DECIMAL(5, 2) DEFAULT NULL COMMENT '温度(℃)',
    `feels_like` DECIMAL(5, 2) DEFAULT NULL COMMENT '体感温度(℃)',
    `humidity` DECIMAL(5, 2) DEFAULT NULL COMMENT '湿度(%)',
    `pressure` DECIMAL(7, 2) DEFAULT NULL COMMENT '气压(hPa)',
    `wind_direction` VARCHAR(20) DEFAULT NULL COMMENT '风向',
    `wind_speed` DECIMAL(5, 2) DEFAULT NULL COMMENT '风速(m/s)',
    `precipitation` DECIMAL(6, 2) DEFAULT NULL COMMENT '降水量(mm)',
    `weather_desc` VARCHAR(50) DEFAULT NULL COMMENT '天气描述',
    `observe_time` DATETIME DEFAULT NULL COMMENT '观测时间',
    `data_source` VARCHAR(20) NOT NULL DEFAULT 'CMA' COMMENT '数据来源',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_city_id` (`city_id`),
    KEY `idx_station_id` (`station_id`),
    KEY `idx_realtime_city_observe` (`city_id`, `observe_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='实况天气';

-- ============================================================
-- 5. 天气预报
-- ============================================================
CREATE TABLE IF NOT EXISTS `weather_forecast` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'ID',
    `city_id` BIGINT NOT NULL COMMENT '城市ID',
    `forecast_type` VARCHAR(10) NOT NULL COMMENT '预报类型: hourly-逐小时, daily-逐日',
    `forecast_time` DATETIME NOT NULL COMMENT '预报目标时间',
    `temperature` DECIMAL(5, 2) DEFAULT NULL COMMENT '温度(℃)',
    `temp_max` DECIMAL(5, 2) DEFAULT NULL COMMENT '最高温(℃)',
    `temp_min` DECIMAL(5, 2) DEFAULT NULL COMMENT '最低温(℃)',
    `humidity` DECIMAL(5, 2) DEFAULT NULL COMMENT '湿度(%)',
    `weather_desc` VARCHAR(50) DEFAULT NULL COMMENT '天气描述',
    `wind_direction` VARCHAR(20) DEFAULT NULL COMMENT '风向',
    `wind_speed` DECIMAL(5, 2) DEFAULT NULL COMMENT '风速(m/s)',
    `pop` DECIMAL(5, 2) DEFAULT NULL COMMENT '降水概率(%)',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_city_id` (`city_id`),
    KEY `idx_forecast_city_type_time` (`city_id`, `forecast_type`, `forecast_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='天气预报';

-- ============================================================
-- 6. 气象预警
-- ============================================================
CREATE TABLE IF NOT EXISTS `weather_warning` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'ID',
    `city_id` BIGINT NOT NULL COMMENT '城市ID',
    `warning_id` VARCHAR(50) DEFAULT NULL COMMENT '官方预警ID',
    `warning_type` VARCHAR(50) DEFAULT NULL COMMENT '预警类型(暴雨/大风等)',
    `warning_level` VARCHAR(20) DEFAULT NULL COMMENT '预警级别(蓝色/黄色/橙色/红色)',
    `title` VARCHAR(200) DEFAULT NULL COMMENT '预警标题',
    `content` TEXT DEFAULT NULL COMMENT '预警内容',
    `publish_time` DATETIME DEFAULT NULL COMMENT '发布时间',
    `effective` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否生效中',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_warning_id` (`warning_id`),
    KEY `idx_city_id` (`city_id`),
    KEY `idx_effective` (`effective`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='气象预警';

-- ============================================================
-- 7. 历史数据同步任务
-- ============================================================
CREATE TABLE IF NOT EXISTS `history_sync_tasks` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '任务ID',
    `station_id` VARCHAR(20) NOT NULL COMMENT '站点ID',
    `start_date` VARCHAR(10) NOT NULL COMMENT '开始日期(YYYY-MM-DD)',
    `end_date` VARCHAR(10) NOT NULL COMMENT '结束日期(YYYY-MM-DD)',
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态: pending-待执行, running-执行中, completed-已完成, failed-失败, stopped-已停止',
    `total_records` INT NOT NULL DEFAULT 0 COMMENT '总记录数',
    `fetched_records` INT NOT NULL DEFAULT 0 COMMENT '已拉取记录数',
    `error_msg` TEXT DEFAULT NULL COMMENT '错误信息',
    `created_by` BIGINT DEFAULT NULL COMMENT '创建人ID',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `completed_at` DATETIME DEFAULT NULL COMMENT '完成时间',
    PRIMARY KEY (`id`),
    KEY `idx_station_id` (`station_id`),
    KEY `idx_status` (`status`),
    KEY `idx_created_by` (`created_by`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='历史数据同步任务';

-- ============================================================
-- 8. 历史气象观测数据（时序数据）
-- ============================================================
CREATE TABLE IF NOT EXISTS `history_observations` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'ID',
    `station_id` VARCHAR(20) NOT NULL COMMENT '站点ID',
    `observe_time` DATETIME NOT NULL COMMENT '观测时间',
    `temperature` DECIMAL(5, 2) DEFAULT NULL COMMENT '温度(℃)',
    `pressure` DECIMAL(7, 2) DEFAULT NULL COMMENT '气压(hPa)',
    `humidity` DECIMAL(5, 2) DEFAULT NULL COMMENT '湿度(%)',
    `wind_direction` DECIMAL(6, 2) DEFAULT NULL COMMENT '风向(°)',
    `wind_speed` DECIMAL(5, 2) DEFAULT NULL COMMENT '风速(m/s)',
    `precipitation` DECIMAL(6, 2) DEFAULT NULL COMMENT '降水量(mm)',
    `is_missing` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否缺测',
    `missing_fields` VARCHAR(200) DEFAULT NULL COMMENT '缺测字段列表',
    `data_source` VARCHAR(20) NOT NULL DEFAULT 'CMA' COMMENT '数据来源',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    -- 分区表要求：分区列(observe_time)必须包含在主键中
    PRIMARY KEY (`id`, `observe_time`),
    UNIQUE KEY `uk_station_time` (`station_id`, `observe_time`),
    KEY `idx_observe_time` (`observe_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='历史气象观测数据'
PARTITION BY RANGE (YEAR(`observe_time`)) (
    PARTITION p_before_2020 VALUES LESS THAN (2020),
    PARTITION p_2020 VALUES LESS THAN (2021),
    PARTITION p_2021 VALUES LESS THAN (2022),
    PARTITION p_2022 VALUES LESS THAN (2023),
    PARTITION p_2023 VALUES LESS THAN (2024),
    PARTITION p_2024 VALUES LESS THAN (2025),
    PARTITION p_2025 VALUES LESS THAN (2026),
    PARTITION p_2026 VALUES LESS THAN (2027),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- ============================================================
-- 9. API 调用日志
-- ============================================================
CREATE TABLE IF NOT EXISTS `api_call_logs` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'ID',
    `endpoint` VARCHAR(200) NOT NULL COMMENT '请求接口',
    `params` VARCHAR(500) DEFAULT NULL COMMENT '请求参数',
    `status_code` INT DEFAULT NULL COMMENT '响应状态码',
    `response_time` INT DEFAULT NULL COMMENT '响应时间(ms)',
    `error_msg` VARCHAR(500) DEFAULT NULL COMMENT '错误信息',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_endpoint` (`endpoint`),
    KEY `idx_status_code` (`status_code`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='API调用日志';

-- ============================================================
-- 9. 空气质量数据
-- ============================================================
CREATE TABLE IF NOT EXISTS `air_quality` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'ID',
    `city_id` BIGINT NOT NULL COMMENT '城市ID',
    `station_id` VARCHAR(20) DEFAULT NULL COMMENT '站点ID',
    `aqi` INT DEFAULT NULL COMMENT 'AQI指数',
    `aqi_level` VARCHAR(20) DEFAULT NULL COMMENT '空气质量等级',
    `aqi_primary` VARCHAR(50) DEFAULT NULL COMMENT '首要污染物',
    `pm25` DECIMAL(7, 2) DEFAULT NULL COMMENT 'PM2.5 (μg/m³)',
    `pm10` DECIMAL(7, 2) DEFAULT NULL COMMENT 'PM10 (μg/m³)',
    `so2` DECIMAL(7, 2) DEFAULT NULL COMMENT 'SO2 (μg/m³)',
    `no2` DECIMAL(7, 2) DEFAULT NULL COMMENT 'NO2 (μg/m³)',
    `co` DECIMAL(7, 3) DEFAULT NULL COMMENT 'CO (mg/m³)',
    `o3` DECIMAL(7, 2) DEFAULT NULL COMMENT 'O3 (μg/m³)',
    `data_type` VARCHAR(20) NOT NULL DEFAULT 'realtime' COMMENT '类型: realtime-实况, forecast-预报',
    `forecast_time` DATETIME DEFAULT NULL COMMENT '预报时间',
    `data_source` VARCHAR(20) NOT NULL DEFAULT 'CMA' COMMENT '数据来源',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_city_id` (`city_id`),
    KEY `idx_station_id` (`station_id`),
    KEY `idx_data_type` (`data_type`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='空气质量数据';

-- ============================================================
-- 10. 生活指数
-- ============================================================
CREATE TABLE IF NOT EXISTS `life_index` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'ID',
    `city_id` BIGINT NOT NULL COMMENT '城市ID',
    `index_type` VARCHAR(30) NOT NULL COMMENT '指数类型(clothing/car_wash/sport/uv/travel等)',
    `index_name` VARCHAR(50) NOT NULL COMMENT '指数名称',
    `index_level` VARCHAR(20) DEFAULT NULL COMMENT '等级',
    `index_desc` VARCHAR(200) DEFAULT NULL COMMENT '描述建议',
    `forecast_date` VARCHAR(10) DEFAULT NULL COMMENT '预报日期',
    `data_source` VARCHAR(20) NOT NULL DEFAULT 'CMA' COMMENT '数据来源',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_city_id` (`city_id`),
    KEY `idx_index_type` (`index_type`),
    KEY `idx_forecast_date` (`forecast_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='生活指数';

-- ============================================================
-- 初始化数据
-- ============================================================

-- 默认管理员账号: admin / admin123 (bcrypt hash)
-- 生产环境务必修改密码
INSERT INTO `users` (`username`, `password_hash`, `real_name`, `is_admin`, `is_active`)
VALUES ('admin', '$2b$12$6L6I2Oo0guREAw8DoEbp/.bqyQ7uXUbPFUcvZf35GmBlgmBLAysNG', '系统管理员', 1, 1)
ON DUPLICATE KEY UPDATE `username` = `username`;

-- 示例城市数据
INSERT INTO `cities` (`city_name`, `city_code`, `station_id`, `province`, `longitude`, `latitude`) VALUES
('北京', '110000', '54511', '北京市', 116.407526, 39.904030),
('上海', '310000', '58367', '上海市', 121.473701, 31.230416),
('广州', '440100', '59287', '广东省', 113.264385, 23.129112),
('深圳', '440300', '59493', '广东省', 114.057868, 22.543099),
('杭州', '330100', '58457', '浙江省', 120.155070, 30.274084),
('成都', '510100', '56294', '四川省', 104.066541, 30.572269),
('武汉', '420100', '57494', '湖北省', 114.305393, 30.593099),
('西安', '610100', '57131', '陕西省', 108.940175, 34.341568),
('南京', '320100', '58238', '江苏省', 118.796877, 32.060255),
('重庆', '500000', '57516', '重庆市', 106.551557, 29.563009)
ON DUPLICATE KEY UPDATE `city_name` = `city_name`;
