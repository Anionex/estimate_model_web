import yaml from 'js-yaml';
import rawConfig from '../../config.yaml?raw';

const parsedConfig = (() => {
    try {
        return yaml.load(rawConfig) || {};
    } catch (error) {
        console.error('Failed to parse config.yaml, falling back to defaults.', error);
        return {};
    }
})();

const backendConfig = parsedConfig.backend || {};
const localBaseUrl = backendConfig.local_base_url || `http://127.0.0.1:${backendConfig.port || 5000}/`;
const productionBaseUrl = backendConfig.production_base_url || localBaseUrl;
const resolvedUrlRoot = import.meta.env.PROD ? productionBaseUrl : localBaseUrl;

export default class ApiUtill{
    static url_root = resolvedUrlRoot;
    static url_gpt="ask_gpt"
    static url_ourmodel="ask_ourmodel"
    static url_xxmodel="ask_xxmodel"
    static url_rating="rate"
}
