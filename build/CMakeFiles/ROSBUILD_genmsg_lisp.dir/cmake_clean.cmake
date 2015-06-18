FILE(REMOVE_RECURSE
  "../msg_gen"
  "../msg_gen"
  "../src/raven_2/msg"
  "CMakeFiles/ROSBUILD_genmsg_lisp"
  "../msg_gen/lisp/raven_automove.lisp"
  "../msg_gen/lisp/_package.lisp"
  "../msg_gen/lisp/_package_raven_automove.lisp"
  "../msg_gen/lisp/raven_state.lisp"
  "../msg_gen/lisp/_package.lisp"
  "../msg_gen/lisp/_package_raven_state.lisp"
)

# Per-language clean rules from dependency scanning.
FOREACH(lang)
  INCLUDE(CMakeFiles/ROSBUILD_genmsg_lisp.dir/cmake_clean_${lang}.cmake OPTIONAL)
ENDFOREACH(lang)
