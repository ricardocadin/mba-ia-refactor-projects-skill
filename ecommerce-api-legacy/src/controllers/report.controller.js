const { financialReportResponse } = require('../views/report.view');

class ReportController {
    constructor(reportService) {
        this.reportService = reportService;
    }

    financialReport = async (req, res) => {
        const report = await this.reportService.financialReport();
        res.json(financialReportResponse(report));
    };
}

module.exports = { ReportController };
