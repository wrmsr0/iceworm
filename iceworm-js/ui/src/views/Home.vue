<template>
  <div class="home">
    <img alt="Vue logo" src="../assets/logo.png">
    <HelloWorld msg="Welcome to Your Vue.js + TypeScript App"/>
    <h1>{{ num }}</h1>
  </div>
</template>

<script lang="ts">
import {Component, Prop, Vue} from 'vue-property-decorator';
import HelloWorld from '@/components/HelloWorld.vue'; // @ is an alias to /src

import { iceworm } from '@/protos/bundle'
const { ServiceWebStatus } = iceworm

@Component({
  components: {
    HelloWorld,
  },
})
export default class Home extends Vue {
  @Prop({default: 0}) private num!: number;

  public timer: ReturnType<typeof setTimeout> | undefined;

  public goBack(): void {
    window.history.length > 1 ? this.$router.go(-1) : this.$router.push('/')
  }

  created() {
    this.fetchEventsList();
    this.timer = setInterval(this.fetchEventsList, 300000)
  }

  fetchEventsList() {
    this.$http.get('/status').then(response => {
      let thing = ServiceWebStatus.fromObject((<any>response).body);
      console.log(thing);
    });
  }

  beforeDestroy() {
    clearInterval(this.timer)
  }

  beforeUpdate() {
    ++this.num
  }
}
</script>
