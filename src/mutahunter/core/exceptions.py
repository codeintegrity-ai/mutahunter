class MutantSurvivedError(Exception):
    pass


class MutantKilledError(Exception):
    pass


class CoverageAnalysisError(Exception):
    pass


class MutationTestingError(Exception):
    pass


class ReportGenerationError(Exception):
    pass


class UnexpectedTestResultError(Exception):
    pass
