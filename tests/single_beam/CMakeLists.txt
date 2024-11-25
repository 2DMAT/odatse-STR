add_test(
  NAME bayes
  COMMAND sh do.sh
  WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}/tests/single_beam/bayes
  )

add_test(
  NAME exchange
  COMMAND sh do.sh
  WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}/tests/single_beam/exchange
  )

add_test(
  NAME mapper
  COMMAND sh do.sh
  WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}/tests/single_beam/mapper
  )

add_test(
  NAME mapper_A2
  COMMAND sh do.sh
  WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}/tests/single_beam/mapper_A2
  )

add_test(
  NAME mapper_B
  COMMAND sh do.sh
  WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}/tests/single_beam/mapper_B
  )

add_test(
  NAME minsearch
  COMMAND sh do.sh
  WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}/tests/single_beam/minsearch
  )

add_test(NAME pamc
  COMMAND sh do.sh
  WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}/tests/single_beam/pamc
  )

