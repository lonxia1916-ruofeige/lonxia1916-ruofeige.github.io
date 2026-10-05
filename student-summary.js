(function () {
  'use strict';
  var data;
  var filter = document.getElementById('summaryFilter');
  function render() {
    var groups = data.classes.filter(function (group) {return !filter.value || filter.value === group.name;});
    var container = document.getElementById('summaryBars');
    container.replaceChildren();
    groups.forEach(function (group) {
      var item = document.createElement('div');
      var label = document.createElement('div');
      label.style.cssText = 'display:flex;justify-content:space-between;gap:15px;margin-bottom:7px;font-size:13px';
      var name = document.createElement('span');
      name.textContent = group.name;
      var count = document.createElement('strong');
      count.textContent = group.count + ' 人';
      label.append(name, count);
      var track = document.createElement('div');
      track.className = 'progress';
      track.style.height = '9px';
      var bar = document.createElement('i');
      bar.style.width = (group.count / data.total * 100) + '%';
      track.appendChild(bar);
      item.append(label, track);
      container.appendChild(item);
    });
    document.getElementById('summaryVisible').textContent = '当前显示 ' + groups.reduce(function (n, group) {return n + group.count;}, 0) + ' 条记录';
  }
  filter.addEventListener('change', function () {if (data) render();});
  fetch('./student-summary.json', {cache:'no-store'}).then(function (response) {
    if (!response.ok) throw new Error('Summary unavailable');
    return response.json();
  }).then(function (result) {
    if (!Array.isArray(result.classes) || result.classes.some(function (g) {return typeof g.name !== 'string' || !Number.isInteger(g.count) || g.count < 0;}) || result.classes.reduce(function (n,g) {return n+g.count;},0) !== result.total) throw new Error('Invalid summary');
    data = result;
    document.getElementById('summaryTotal').textContent = data.total;
    document.getElementById('summaryClasses').textContent = data.classes.filter(function (g) {return g.name !== '未填写';}).length;
    document.getElementById('summaryMissing').textContent = data.classes.filter(function (g) {return g.name === '未填写';}).reduce(function (n,g) {return n+g.count;},0);
    document.getElementById('summaryTime').textContent = '导出时间：' + data.exportedAt;
    data.classes.forEach(function (group) {
      var option = document.createElement('option');
      option.value = group.name;
      option.textContent = group.name + '（' + group.count + '）';
      filter.appendChild(option);
    });
    document.getElementById('summaryNote').textContent = '依据最新名单导出，“使用中”为平台记录状态，不代表已核实个人学习进度。条形长度表示占全部记录的比例。“示例班级”按原字段保留。此名单汇总为导出快照，尚未自动更新。';
    render();
  }).catch(function () {
    document.getElementById('summaryNote').textContent = '汇总读取失败，请刷新重试。';
  });
})();
