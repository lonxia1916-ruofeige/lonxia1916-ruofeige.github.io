(function () {
  'use strict';
  var inFlight = false;
  function text(id, value) { var el = document.getElementById(id); if (el) el.textContent = value; }
  function valid(data) {
    return data && typeof data.updated === 'string' && Array.isArray(data.tasks) &&
      data.tasks.every(function (t) {
        return typeof t.id === 'string' && typeof t.name === 'string' &&
          typeof t.dates === 'string' && /^\d+(\.\d+)?%$/.test(t.rate) &&
          /^\d+(\.\d+)?%$/.test(t.completion);
      });
  }
  function describe(data) {
    var verified = data.tasks.filter(function (t) { return t.verified; });
    var records = verified.reduce(function (n, t) { return n + (t.verifiedCount || 0); }, 0);
    var stamp = data.updatedAt || data.updated;
    text('readingHomeSummary', '数据时间：' + stamp + ' · ' + data.tasks.length + '项进行中 · ' + verified.length + '项详情已核实（' + records + '条记录），' + (data.tasks.length - verified.length) + '项详情尚未读取。');
    text('readingViewSummary', '仅展示进行中的任务 · 最近成功读取：' + stamp + ' · 源数据计划每天上午9点（北京时间）同步；网页每60秒检查最新数据。');
    text('readingCoverage', verified.length + '项详情已核实，合计' + records + '条记录；其余' + (data.tasks.length - verified.length) + '项保留任务汇总。今天尚未结束，未打卡不直接等于逾期；打卡率不等于阅读理解能力。');
    text('readingDataNote', '阅读任务最近成功读取：' + stamp + '。来源读取需本地应用运行且平台登录有效；平台热点尚未接入。');
    text('readingSnapshotNote', '当前为最近成功读取的数据。今天尚未结束，未打卡不直接等于逾期；打卡率不等于阅读理解能力。');
    text('readingGoTasks', '查看' + data.tasks.length + '项阅读任务与复制提醒');
    text('readingFeedCurrent', '本次已核实' + records + '条详情记录。具体提交情况请在学员后台核对；未核实详情不沿用旧记录。');
  }
  async function refresh() {
    if (inFlight) return;
    inFlight = true;
    try {
      var response = await fetch('./reading-tasks.json?t=' + Date.now(), {cache: 'no-store'});
      if (!response.ok) throw new Error('HTTP ' + response.status);
      var data = await response.json();
      if (!valid(data)) throw new Error('数据格式不完整');
      var changed = JSON.stringify(data) !== JSON.stringify(READING_TASK_DATA);
      if (changed) {
        READING_TASK_DATA = data;
        var choice = document.getElementById('readingTaskChoice');
        var previous = choice.value;
        choice.innerHTML = data.tasks.map(function (t) {
          return '<option value="' + esc(t.id) + '">' + esc(t.id + ' · ' + t.name + ' · ' + t.dates) + '</option>';
        }).join('');
        if (data.tasks.some(function (t) { return t.id === previous; })) choice.value = previous;
        else {
          document.getElementById('readingReminder').value = data.tasks.length ? readingReminder(data.tasks[0]) : '';
          text('readingCopyStatus', data.tasks.length ? '任务列表已更新，请核对当前提醒。' : '当前无进行中任务。');
        }
        renderStudents();
      }
      describe(data);
      if (!data.updatedAt) { text('readingSyncStatus', '已加载历史快照；尚无自动同步成功时间。'); return; }
      var age = Date.now() - Date.parse(data.updatedAt);
      text('readingSyncStatus', age > 26 * 60 * 60 * 1000 ? '网站数据已加载；源数据超过26小时未成功更新，请检查本地同步及登录状态。' : '网站已加载最近成功数据；每60秒检查更新。');
    } catch (error) {
      text('readingSyncStatus', '读取最新网站数据失败，保留已显示的数据。可稍后重试。');
    } finally { inFlight = false; }
  }
  describe(READING_TASK_DATA);
  document.getElementById('refreshReadingData').addEventListener('click', refresh);
  document.addEventListener('visibilitychange', function () { if (!document.hidden) refresh(); });
  refresh();
  setInterval(function () { if (!document.hidden) refresh(); }, 60000);
})();
