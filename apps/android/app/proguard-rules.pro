# Keep kotlinx.serialization and Room generated code for release builds.
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.**
-keepclassmembers class com.openjiuwen.knowledge.data.** { *; }
