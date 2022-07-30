import { axisBottom, axisRight, format, scaleLinear } from "d3";
import { subtract } from "../utils";

function histogram() {
  let margin = { top: 0, right: 0, bottom: 0, left: 0 };
  let xFormat = format(",");
  let xScale = scaleLinear();
  let yFormat = format(",");
  let yScale = scaleLinear();

  function chart(context) {
    const height = Math.abs(yScale.range().reduce(subtract, 0));
    const width = Math.abs(xScale.range().reduce(subtract, 0));
    const fontSize = parseInt(getComputedStyle(context.node()).fontSize);

    const xAxis = axisBottom(xScale).tickFormat(xFormat);
    const yAxis = axisRight(yScale)
      .ticks(height / fontSize / 2)
      .tickFormat(yFormat)
      .tickSize(width + margin.left + margin.right);

    const container = context
      .selectAll(".data")
      .data([null])
      .join((enter) => enter.insert("g").attr("class", "data"));

    container
      .selectAll("rect")
      .data(context.datum())
      .join("rect")
      .attr("x", (d) => xScale(d.x0))
      .attr("y", (d) => yScale(d.length))
      .attr("width", (d) => xScale(d.x1) - xScale(d.x0))
      .attr("height", (d) => yScale(0) - yScale(d.length));

    context
      .selectAll(".x-axis")
      .data([null])
      .join((enter) => enter.insert("g").attr("class", "x-axis"))
      .attr("transform", `translate(0, ${height})`)
      .call(xAxis);

    context
      .selectAll(".y-axis")
      .data([null])
      .join((enter) => enter.insert("g").attr("class", "y-axis"))
      .call(yAxis)
      .call((g) => {
        g.select(".domain").remove();
        g.selectAll(".tick text").attr("x", 4).attr("dy", -4);
      });
  }

  chart.margin = function (newMargin) {
    // Make sure we return a copy of our margin object so that the margin can't
    // be changed outside of the chart by mistake.
    if (!newMargin) return Object.assign({}, margin);
    Object.assign(margin, newMargin);
    return chart;
  };

  chart.xFormat = function (fmt) {
    if (!fmt) return xFormat;
    xFormat = format(fmt);
    return chart;
  };

  chart.xScale = function (scale) {
    if (!scale) return xScale;
    xScale = scale;
    return chart;
  };

  chart.yFormat = function (fmt) {
    if (!fmt) return yFormat;
    yFormat = format(fmt);
    return chart;
  };

  chart.yScale = function (scale) {
    if (!scale) return yScale;
    yScale = scale;
    return chart;
  };

  return chart;
}

export default histogram;
