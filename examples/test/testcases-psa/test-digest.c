// SPDX-License-Identifier: Apache-2.0
// Copyright 2018 Eotvos Lorand University, Budapest, Hungary

#include "test.h"

fake_cmd_t t4p4s_testcase_test[][RTE_MAX_LCORE] = {
    {                
        {FAKE_PKT, 0, 1, {"01", ""}, 200, 12345, {"01", ""}},
        {FAKE_PKT, 0, 1, {"02", ""}, 200, 12345, {"02", ""}}, 
        FEND,
    },
    {
    FEND,
    },
};

testcase_t t4p4s_test_suite[MAX_TESTCASES] = {
    { "test",           &t4p4s_testcase_test },
    TEST_SUITE_END,
};