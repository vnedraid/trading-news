import type { AxiosInstance } from "axios";
import { instance } from "../shared/api";

export class Api {
  constructor(public instance: AxiosInstance) {}
}

export default new Api(instance);
