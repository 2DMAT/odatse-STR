add_test(
  NAME mapper_weight_calc_A
  COMMAND sh do.sh
  WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}/tests/many_beam/mapper_weight_calc_A
  )

add_test(
  NAME mapper_weight_calc_A2
  COMMAND sh do.sh
  WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}/tests/many_beam/mapper_weight_calc_A2
  )

add_test(
  NAME mapper_weight_manual
  COMMAND sh do.sh
  WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}/tests/many_beam/mapper_weight_manual
  )

if (FULLTEST)
add_test(
  NAME minsearch_weight_calc
  COMMAND sh do.sh
  WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}/tests/many_beam/minsearch_weight_calc
  )

add_test(
  NAME minsearch_weight_manual
  COMMAND sh do.sh
  WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}/tests/many_beam/minsearch_weight_manual
  )
endif()
