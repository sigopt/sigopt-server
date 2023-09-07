# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion


# TODO: Come up with a way to test this without hardcoding desired suggestion source
EXPECTED_GP_OPTIMIZATION_SOURCE = UnprocessedSuggestion.Source.GP_CATEGORICAL
CREATE_USER_EMAIL_SEARCH_TERM = "Please create an account"
NEW_USER_EMAIL_SEARCH_TERM = "Thanks for choosing SigOpt!"
OWNER_INVITE_EMAIL_SEARCH_TERM = "As an owner you will have full access"
VERIFY_EMAIL_SEARCH_TERM = "you want to use this email address"
