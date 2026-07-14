from pptx.oxml.ns import qn
from pptx.oxml.xmlchemy import OxmlElement


def set_cell_border(
    cell,
    color,
    width="12700",
):
    color_hex = "".join(
        f"{component:02X}"
        for component in color
    )

    tc_pr = cell._tc.get_or_add_tcPr()

    for edge_name in (
        "a:lnL",
        "a:lnR",
        "a:lnT",
        "a:lnB",
    ):
        old_edge = tc_pr.find(qn(edge_name))

        if old_edge is not None:
            tc_pr.remove(old_edge)

        edge = OxmlElement(edge_name)
        edge.set("w", width)

        solid_fill = OxmlElement("a:solidFill")
        color_element = OxmlElement("a:srgbClr")
        color_element.set("val", color_hex)
        solid_fill.append(color_element)
        edge.append(solid_fill)

        dash = OxmlElement("a:prstDash")
        dash.set("val", "solid")
        edge.append(dash)

        tc_pr.append(edge)