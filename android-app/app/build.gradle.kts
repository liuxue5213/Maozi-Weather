plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("org.jetbrains.kotlin.plugin.serialization")
    id("org.jetbrains.kotlin.kapt")  // 用于 Room 注解处理
}

android {
    namespace = "com.maozi.weather"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.maozi.weather"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "0.1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        // 后端基础地址：默认模拟器访问宿主机；
        // 真机调试时用 -PdevBaseUrl=http://<电脑局域网IP>:60245/ 覆盖
        val devBaseUrl: String =
            (project.findProperty("devBaseUrl") as String?) ?: "http://10.0.2.2:60245/"
        buildConfigField("String", "BASE_URL", "\"$devBaseUrl\"")
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            // 生产环境后端地址
            buildConfigField("String", "BASE_URL", "\"https://api.maozi-weather.com/\"")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }
}

dependencies {
    // Compose BOM
    val composeBom = platform("androidx.compose:compose-bom:2024.09.00")
    implementation(composeBom)

    // Compose UI
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")

    // Activity & Lifecycle
    implementation("androidx.activity:activity-compose:1.9.2")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.5")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.5")

    // Navigation
    implementation("androidx.navigation:navigation-compose:2.8.0")

    // Core
    implementation("androidx.core:core-ktx:1.13.1")

    // Network: Retrofit + OkHttp + Kotlinx Serialization
    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.1")
    implementation("com.jakewharton.retrofit:retrofit2-kotlinx-serialization-converter:1.0.0")

    // Room (本地缓存) - 使用 kapt 处理注解
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    kapt("androidx.room:room-compiler:2.6.1")

    // DataStore (偏好设置)
    implementation("androidx.datastore:datastore-preferences:1.1.1")

    // Coil (图片加载)
    implementation("io.coil-kt:coil-compose:2.7.0")

    // WorkManager (后台任务)
    implementation("androidx.work:work-runtime-ktx:2.9.1")

    // Glance 桌面小组件
    implementation("androidx.glance:glance-appwidget:1.0.0")
    debugImplementation("androidx.glance:glance-appwidget-preview:1.0.0")

    // 测试
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation(composeBom)
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
