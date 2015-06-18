FILE(REMOVE_RECURSE
  "../msg_gen"
  "../msg_gen"
  "../src/raven_2/msg"
  "CMakeFiles/ROSBUILD_gencfg_cpp"
  "../cfg/cpp/raven_2/MyStuffConfig.h"
  "../docs/MyStuffConfig.dox"
  "../docs/MyStuffConfig-usage.dox"
  "../src/raven_2/cfg/MyStuffConfig.py"
  "../docs/MyStuffConfig.wikidoc"
)

# Per-language clean rules from dependency scanning.
FOREACH(lang)
  INCLUDE(CMakeFiles/ROSBUILD_gencfg_cpp.dir/cmake_clean_${lang}.cmake OPTIONAL)
ENDFOREACH(lang)
