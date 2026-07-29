from __future__ import annotations

from src.database.session import get_session
from src.framework.base_service import BaseService
from src.models.production_assignment import (
    ProductionAssignment,
)
from src.models.production_execution import (
    ProductionExecution,
)
from src.models.production_ng import ProductionNG
from src.models.production_order import ProductionOrder
from src.services.oee_pareto_service import (
    OEEParetoService,
    ParetoFilter,
)


class NGRow:
    """
    Một bản ghi NG đã được ghép (join) với Machine/Product/Work Order -
    dùng làm input cho `OEEParetoService`, và cũng đủ thông tin để hiển
    thị trực tiếp lên bảng chi tiết của màn hình NG Analysis.

    Đây KHÔNG phải là SQLAlchemy model - chỉ là một "dòng đã join sẵn",
    tương tự cách `ProductionNGController.load_records()` join thủ công
    để hiển thị lên `ProductionNGPage`.
    """

    __slots__ = (
        "id",
        "reason_code",
        "reason_name",
        "quantity",
        "ng_type",
        "recorded_at",
        "root_cause",
        "product_code",
        "machine_code",
        "work_order_no",
        "employee_code",
    )

    def __init__(
        self,
        *,
        id,
        reason_code,
        reason_name,
        quantity,
        ng_type,
        recorded_at,
        root_cause,
        product_code,
        machine_code,
        work_order_no,
        employee_code,
    ):
        self.id = id
        self.reason_code = reason_code
        self.reason_name = reason_name
        self.quantity = quantity
        self.ng_type = ng_type
        self.recorded_at = recorded_at
        self.root_cause = root_cause
        self.product_code = product_code
        self.machine_code = machine_code
        self.work_order_no = work_order_no
        self.employee_code = employee_code


class NGAnalysisService(BaseService):
    """
    Giai đoạn 6 (Quality, 2026-07-25): nối hạ tầng Pareto có sẵn
    (`OEEParetoService`, trước đó chỉ dùng cho OEE Dashboard, nguồn dữ
    liệu là `ProductionLog`) với bảng `ProductionNG` THẬT - trước đây
    không có tầng nào làm việc này, mỗi bản ghi NG chỉ hiển thị dạng
    danh sách phẳng trên `ProductionNGPage`, không có phân tích Pareto
    theo lý do/sản phẩm/máy/nhân viên.
    """

    def __init__(
        self,
        session=None,
        pareto_service=None,
    ):
        super().__init__()

        self._owns_session = session is None
        self.session = session or get_session()

        self.pareto_service = (
            pareto_service or OEEParetoService()
        )

    # ==========================================================
    # Data loading (join NG -> Execution -> Assignment -> Order)
    # ==========================================================

    def load_ng_rows(self) -> list[NGRow]:
        records = (
            self.session
            .query(ProductionNG)
            .filter(ProductionNG.status == "ACTIVE")
            .all()
        )

        rows = []

        for record in records:
            execution = (
                self.session
                .query(ProductionExecution)
                .filter(
                    ProductionExecution.id
                    == record.execution_id
                )
                .first()
            )

            assignment = None
            production_order = None

            if execution is not None:
                assignment = (
                    self.session
                    .query(ProductionAssignment)
                    .filter(
                        ProductionAssignment.id
                        == execution.assignment_id
                    )
                    .first()
                )

            if assignment is not None:
                production_order = (
                    self.session
                    .query(ProductionOrder)
                    .filter(
                        ProductionOrder.id
                        == assignment.production_order_id
                    )
                    .first()
                )

            rows.append(
                NGRow(
                    id=record.id,
                    reason_code=record.reason_code,
                    reason_name=record.reason_name,
                    quantity=record.quantity,
                    ng_type=record.ng_type,
                    recorded_at=record.recorded_at,
                    root_cause=record.root_cause,
                    product_code=(
                        production_order.product_code
                        if production_order
                        else None
                    ),
                    machine_code=(
                        assignment.machine_code
                        if assignment
                        else None
                    ),
                    work_order_no=(
                        production_order.work_order_no
                        if production_order
                        else None
                    ),
                    employee_code=record.employee_code,
                )
            )

        return rows

    # ==========================================================
    # Pareto
    # ==========================================================

    def build_reason_pareto(
        self,
        rows=None,
        *,
        maximum_items=None,
        focus_threshold=80.0,
    ):
        """
        Pareto số lượng NG theo lý do (reason_name).
        """
        return self._build_pareto(
            rows,
            label_fields=("reason_name",),
            maximum_items=maximum_items,
            focus_threshold=focus_threshold,
        )

    def build_product_pareto(
        self,
        rows=None,
        *,
        maximum_items=None,
        focus_threshold=80.0,
    ):
        """
        Pareto số lượng NG theo sản phẩm.
        """
        return self._build_pareto(
            rows,
            label_fields=("product_code",),
            maximum_items=maximum_items,
            focus_threshold=focus_threshold,
        )

    def build_machine_pareto(
        self,
        rows=None,
        *,
        maximum_items=None,
        focus_threshold=80.0,
    ):
        """
        Pareto số lượng NG theo máy.
        """
        return self._build_pareto(
            rows,
            label_fields=("machine_code",),
            maximum_items=maximum_items,
            focus_threshold=focus_threshold,
        )

    def _build_pareto(
        self,
        rows,
        *,
        label_fields,
        maximum_items,
        focus_threshold,
    ):
        rows = (
            rows
            if rows is not None
            else self.load_ng_rows()
        )

        return self.pareto_service.build_generic_pareto(
            records=rows,
            label_fields=label_fields,
            value_fields=("quantity",),
            filters=ParetoFilter(),
            maximum_items=maximum_items,
            focus_threshold=focus_threshold,
            unknown_label="Không xác định",
        )

    # ==========================================================
    # Transaction (read-only service, nhưng vẫn hỗ trợ close() an
    # toàn theo đúng pattern chung của app)
    # ==========================================================

    def close(self):
        if self._owns_session and self.session is not None:
            try:
                self.session.commit()
            except Exception:
                self.session.rollback()
                raise
            finally:
                self.session.close()
