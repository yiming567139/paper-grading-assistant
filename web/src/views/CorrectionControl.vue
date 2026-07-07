<script setup lang="ts">
import ProcessControl from '@/components/business/ProcessControl.vue'
import CorrectionLog from '@/components/business/CorrectionLog.vue'
</script>

<template>
  <div class="page">
    <div class="content-wrapper">
      <ProcessControl />
      <div class="spacer"></div>
      <CorrectionLog />
    </div>
  </div>
</template>

<style scoped>
.content-wrapper {
  max-width: 100%;
  margin: 0 auto;
}

.spacer {
  height: 16px; /* 流程控制和批改日志间距 */
}
</style>
